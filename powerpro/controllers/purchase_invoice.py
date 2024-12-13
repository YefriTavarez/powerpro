# Copyright (c) 2024, Rainier J  Polanco and Contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cint
from frappe.utils import flt


def validate(doc, event):
    set_taxes(doc)
    calculate_totals(doc)
    valid_prefix(doc)
    validate_rnc(doc)
    validate_retention_type(doc)

    tax_category = frappe.db.get_value("Supplier", doc.supplier, "tax_category")
    if not tax_category:
        educate_user_about_missing_tax_category()


def before_submit(doc, event):
    validate_duplicate_ncf(doc)
    assign_informal_supplier_ncf(doc)


def calculate_totals(doc):
    total_bienes = total_servicios = 0.000

    for item in doc.items:
        if item.item_type == "Bienes":
            total_bienes += item.base_amount

        if item.item_type == "Servicios":
            total_servicios += item.base_amount

    doc.monto_facturado_bienes = total_bienes
    doc.monto_facturado_servicios = total_servicios


def assign_informal_supplier_ncf(doc):
    # si ya tiene un NCF asignado, no hacer nada
    if doc.ncf and doc.amended_from:
        # si es una factura rectificativa, no hacer nada
        return # salir de la función


    # traer la Categoría de Impuestos del proveedor
    tax_category = frappe.db.get_value("Supplier", doc.supplier, "tax_category")

    # si no tiene categoría de impuestos asignada, mostrar un mensaje de advertencia
    # y salir de la función
    if not tax_category:
        educate_user_about_missing_tax_category()
        return # salir de la función

    # traer la Categoría de Impuestos no formales para comparar
    # si el proveedor es informal y generar su respectivo NCF
    informal_tax_category = frappe.db.get_single_value(
        "DGII Settings", "non_formal_tax_category"
    )

    ncf_serie = None

    # si el proveedor es informal, leer la configuracion en el modulo NCF Manager
    # para obtener la serie de comprobantes a utilizar
    if tax_category == informal_tax_category:
        if doc.ncf and doc.amended_from:
            # si no es una factura rectificativa, mostrar un mensaje de advertencia
            frappe.msgprint(
                """
                <p>
                Esta factura ya tiene un NCF asignado. Y no se ha detectado que sea una factura rectificativa.
                Se procederá a sobre-escribir el NCF actual. 
                </p>
                """, alert=True
            )

        if name := frappe.db.exists(
            "NCF Manager",
            {
                "company": doc.company,
                "tax_category": informal_tax_category,
            }
        ):
            ncf_serie = frappe.get_doc("NCF Manager", name)
        else:
            frappe.throw(
                f"No se ha configurado un registro en el módulo 'NCF Manager' para manejar los comprobantes para la 'Categoría de Impuestos: {tax_category}'"
            )
    else:
        # solo se generan NCF para proveedores informales (creo que tambien para gastos menores, pero eso es en otro episodio)
        return # salir de la función

    current = cint(ncf_serie.current)

    if cint(ncf_serie.top) and current >= cint(ncf_serie.top):
        frappe.throw(
            f"Ha llegado al máximo establecido para la serie de comprobantes {ncf_serie.name!r}!"
        )

    current += 1

    ncf_serie.current = current
    ncf_serie.db_update()

    doc.ncf = "{0}{1:08d}".format(ncf_serie.serie.split(".")[0], current)
    doc.vencimiento_ncf = ncf_serie.expiration
    # doc.db_update() # no es necesario, ya que el documento se actualiza automaticamente al finalizar la funcion


def get_serie_for_(doc):
    supplier_category = frappe.get_value("Supplier", doc.supplier, "tax_category")
    if not supplier_category:
        frappe.throw(
            """Favor seleccionar una categoría de impuestos para el 
            suplidor <a href='/desk#Form/Supplier/{0}'>{0}</a>""".format(
                doc.supplier_name
            )
        )

    filters = {
        "company": doc.company,
        "tax_category": supplier_category,
        # "serie": "B11.##########"
    }
    if not frappe.db.exists("NCF Manager", filters):
        frappe.throw(
            "No existe una secuencia de NCF para el tipo {}".format(supplier_category)
        )

    return frappe.get_doc("NCF Manager", filters)


def set_taxes(doc):
    dgi_setting = frappe.get_single("DGII Settings")

    total_tip = total_excise = 0.000

    if dgi_setting.multi_company:
        for row in dgi_setting.multi_company:
            if row.company == doc.company:
                total_tip = sum(
                    tax.base_tax_amount_after_discount_amount
                    for tax in doc.taxes
                    if tax.account_head == row.itbis_account
                )
                doc.total_itbis = total_tip

                total_tip = sum(
                    tax.base_tax_amount_after_discount_amount
                    for tax in doc.taxes
                    if tax.account_head == row.legal_tip_account
                )
                doc.legal_tip = total_tip

                total_excise = sum(
                    tax.base_tax_amount_after_discount_amount
                    for tax in doc.taxes
                    if tax.account_head == row.excise_tax
                )
                doc.excise_tax = total_excise

                return

    if dgi_setting.itbis_account:
        total_tip = sum(
            [
                row.base_tax_amount_after_discount_amount
                for row in filter(
                    lambda x: x.account_head == dgi_setting.itbis_account, doc.taxes
                )
            ]
        )
        doc.total_itbis = total_tip

    if dgi_setting.legal_tip_account:
        total_tip = sum(
            [
                row.base_tax_amount_after_discount_amount
                for row in filter(
                    lambda x: x.account_head == dgi_setting.legal_tip_account, doc.taxes
                )
            ]
        )
        doc.legal_tip = total_tip

    if dgi_setting.excise_tax:
        total_excise = sum(
            [
                row.base_tax_amount_after_discount_amount
                for row in filter(
                    lambda x: x.account_head == dgi_setting.excise_tax, doc.taxes
                )
            ]
        )
        doc.excise_tax = total_excise

    if dgi_setting.other_tax_detail:
        for tax in dgi_setting.other_tax_detail:
            total_amount = 0.000
            total_amount = sum(
                [
                    row.base_tax_amount_after_discount_amount
                    for row in filter(
                        lambda x: x.account_head == tax.account, doc.taxes
                    )
                ]
            )
            doc.set(tax.tax_type, total_amount)


def validate_duplicate_ncf(doc):
    if not doc.ncf:
        return

    filters = {
        "tax_id": doc.tax_id,
        "ncf": doc.ncf,
        "docstatus": ["!=", 2],
        "name": ["!=", doc.name],
    }
    if frappe.db.exists("Purchase Invoice", filters):
        frappe.throw(
            """
            Ya existe una factura registrada a nombre de <b>{supplier_name}</b> 
            con el mismo NCF <b>{ncf}</b>, favor verificar!
        """.format(
                **doc.as_dict()
            )
        )


def validate_retention_type(doc):
    conf = frappe.get_doc("DGII Settings")
    # if not hasattr(conf, "dgii_settings_multi_company"):
    # 	return

    matched_other_rows = list(
        filter(
            lambda x, comp=doc.company: x.company == comp
            and x.tax_type == "itbis_retenido",
            conf.multi_other_tax_detail,
        )
    )

    matched_accounts = set([t.account_head for t in doc.taxes]).intersection(
        [d.account for d in matched_other_rows]
    )

    # if not matched_accounts and doc.include_retention:
    #     frappe.throw("Marcaste la casilla de incluir retención de ITBIS, pero no se encontró una cuenta de retención de ITBIS configurada para esta empresa")
    if matched_accounts and not doc.include_retention:
        frappe.throw(
            f"""
            No marcaste la casilla de incluir retención de ITBIS, pero se encontraron cuentas de retención de ITBIS configuradas para esta empresa.
               <br><ul>{'<li>{}</li>'.join(matched_accounts)}</ul>
        """
        )

    doc.itbis_retenido = sum(
        [
            tax.base_tax_amount_after_discount_amount
            for tax in doc.taxes
            if tax.account_head in matched_accounts
        ]
    )


def valid_prefix(doc):
    if not doc.ncf:
        return
    ncf_quantity = 0
    ncf_quantity = len(doc.ncf)
    valid_prefix = [
        "B01",
        "B02",
        "B03",
        "B04",
        "B11",
        "B13",
        "B14",
        "B15",
        "E31",
        "E33",
        "E34",
    ]
    if ncf_quantity != 11 and ncf_quantity != 13:
        frappe.throw(
            f"El numero de comprobante tiene <b>{ncf_quantity}</b> caracteres, deben ser <b>11</b> o <b>13</b> para la serie E."
        )

    if not doc.ncf[:3] in valid_prefix:
        frappe.throw(f"El prefijo <b>{doc.ncf[:3]}</b> no es valido, favor verificar!")


def validate_rnc(doc):
    if not doc.tax_id:
        return

    len_tax_id = len(doc.tax_id)

    if len_tax_id == 9 or len_tax_id == 11:
        return

    frappe.throw("El RNC/Cédula debe tener 9 o 11 caracteres")


@frappe.whitelist()
def get_retention_details(base_total_taxes_and_charges, total, retention_type):
    # Si la retención es ITBIS o ISR, calcular el monto correspondiente
    retention = frappe.get_doc("Retention", retention_type)

    if retention.retention_type == "ITBIS":
        amount = (
            flt(base_total_taxes_and_charges, 2)
            * flt(retention.retention_rate, 2)
            / 100.0
        )
    else:
        amount = flt(total, 2) * flt(retention.retention_rate, 2) / 100.0

    return {
        "amount": amount,
    }


def educate_user_about_missing_tax_category():
    frappe.msgprint(
        """
        <p>
        El proveedor seleccionado no tiene una categoría de impuestos asignada. 
        Esto puede ser aceptable si se trata de un proveedor internacional, pero es importante que
        el sistema lo refleje correctamente para evitar ambigüedades.
        </p>

        <p>
        Por favor, asegúrate de asignar la categoría de impuestos correspondiente. Para proveedores 
        internacionales, selecciona una categoría que indique explícitamente su condición (por ejemplo, 
        “Internacional - Exento”). Esto garantiza una correcta clasificación y trazabilidad en el sistema.
        </p>
        """, alert=True, indicator="yellow"
    )