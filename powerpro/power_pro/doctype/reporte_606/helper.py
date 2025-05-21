# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

from typing import Union

import frappe


ncf_modificados = None


def get_ncf_modificado(
    invoice_id=None, from_date=None, to_date=None, company=None
) -> str:
    """NCF Modificado

    En “NCF Modificado” registre el NCF del comprobante que fue modificado por la
    factura. Este campo no estará habilitado hasta tanto no existan normativas que
    establezcan un régimen de retención u obliguen a los contribuyentes a realizar la
    misma.
    """

    def generator():
        return dict(
            frappe.db.sql(
                f"""
                    Select
                        credit.name As invoice_id,
                        original.ncf As ncf_modificado
                    From
                        `tabPurchase Invoice` As credit
                    Inner Join
                        `tabPurchase Invoice` As original
                        On original.name = credit.return_against
                        And original.docstatus = credit.docstatus
                    Where
                        credit.docstatus = 1
                        And (
                            original.posting_date Between {from_date!r} And {to_date!r}
                            Or credit.posting_date Between {from_date!r} And {to_date!r}
                        )
                """
            )
        )

    global ncf_modificados
    if ncf_modificados is None:
        ncf_modificados = generator()

    return ncf_modificados.get(invoice_id, "") if invoice_id else ncf_modificados


# globals
itbis_facturado = None


def get_itbis_facturado(
    invoice_id=None, from_date=None, to_date=None, company=None
) -> float:
    """Will fetch all invoices in the date range and company provided (given via filters).
    Then will sum all the ITBIS amounts grouped by the invoice id.
    """

    # either invoice_id or (from_date and to_date) must be provided
    if not invoice_id and (not from_date or not to_date):
        frappe.throw(
            "Either invoice_id or (from_date and to_date and company) must be provided"
        )

    def generator():
        company_filter = str()
        if company:
            company_filter = f"And parent.company = {company!r}"

        return dict(
            frappe.db.sql(
                f"""
                    Select
                        parent.name As invoice_id,
                        Sum(child.base_tax_amount) As amount
                    From
                        `tabPurchase Taxes and Charges` As  child
                    Inner Join
                        `tabPurchase Invoice` As  parent
                        On
                            child.parenttype = "Purchase Invoice"
                            And child.parentfield = "taxes"
                            And child.parent = parent.name
                            And child.docstatus = parent.docstatus
                            And child.dominican_tax_type = "ITBIS"
                            And child.add_deduct_tax = "Add"
                    Where
                        parent.docstatus = 1
                        {company_filter}
                        And parent.posting_date Between {from_date!r} And {to_date!r}
                        And parent.is_opening = "No"
                    Group by
                        parent.name
                """
            )
        )

    global itbis_facturado
    if itbis_facturado is None:
        itbis_facturado = generator()
    
    return itbis_facturado.get(invoice_id, 0.0) if invoice_id else sum(itbis_facturado.values())


itbis_retenido = None


def get_itbis_retenido(
    invoice_id=None, from_date=None, to_date=None, company=None
) -> float:
    """Will fetch all invoices in the date range and company provided (given via filters).
    Then will sum all the ITBIS amounts grouped by the invoice id.
    """

    # either invoice_id or (from_date and to_date) must be provided
    if not invoice_id and (not from_date or not to_date):
        frappe.throw(
            "Either invoice_id or (from_date and to_date and company) must be provided"
        )

    def generator():
        company_filter = str()
        if company:
            company_filter = f"And parent.company = {company!r}"

        return dict(
            frappe.db.sql(
                f"""
                    Select
                        parent.name As invoice_id,
                        Sum(-child.base_tax_amount) As amount
                    From
                        `tabPurchase Taxes and Charges` As  child
                    Inner Join
                        `tabPurchase Invoice` As  parent
                        On
                            child.parenttype = "Purchase Invoice"
                            And child.parentfield = "taxes"
                            And child.parent = parent.name
                            And child.docstatus = parent.docstatus
                            And child.dominican_tax_type = "ITBIS"
                            And child.add_deduct_tax = "Deduct"
                    Where
                        parent.docstatus = 1
                        {company_filter}
                        And parent.posting_date Between {from_date!r} And {to_date!r}
                        And parent.is_opening = "No"
                    Group by
                        parent.name
                """
            )
        )

    global itbis_retenido
    if itbis_retenido is None:
        itbis_retenido = generator()
    
    return itbis_retenido.get(invoice_id, 0.0) if invoice_id else sum(itbis_retenido.values())


def get_itbis_sujeto_proporcionalidad(
    invoice_id=None, from_date=None, to_date=None, company=None
) -> Union[float, str]:
    """ITBIS sujeto a Proporcionalidad (Art. 349)

    En “ITBIS sujeto a Proporcionalidad (Art. 349)” registre el valor del ITBIS que
    estará sujeto al cálculo de la proporcionalidad, según el Art. 349 de la Ley No.
    11-92. La sumatoria de esta columna será el valor que deberá distribuir en el Anexo
    A del Formulario de ITBIS como el ITBIS SUJETO A PROPORCIONALIDAD.
    """

    return ""


def get_itbis_llevado_costo(
    invoice_id=None, from_date=None, to_date=None, company=None
) -> float:
    """ITBIS llevado al Costo

    En “ITBIS llevado al Costo” coloque el valor del ITBIS que es llevado
    directamente al Costo, es decir, que no se va a deducir como adelanto en la
    Declaración Jurada de ITBIS y que se utilizará como costo en la Declaración Jurada de
    Impuesto Sobre la Renta. En esta columna no debe colocar el ITBIS no admitido por
    Proporcionalidad.
    """

    return 0.0


def get_itbis_adelantado(
    invoice_id=None, from_date=None, to_date=None, company=None
) -> float:
    """ITBIS por Adelantar

    El campo “ITBIS por Adelantar” se completará automáticamente al momento de
    validar el archivo. Resulta al restar el valor del campo “ITBIS Facturado” menos el
    valor del campo “ITBIS llevado al Costo” del mismo registro
    """

    return get_itbis_facturado(
        invoice_id=invoice_id, from_date=from_date, to_date=to_date, company=company
    ) - get_itbis_llevado_costo(
        invoice_id=invoice_id, from_date=from_date, to_date=to_date, company=company
    )


def get_itbis_percibido(
    invoice_id=None, from_date=None, to_date=None, company=None
) -> Union[float, str]:
    """ITBIS percibido en compras

    En “ITBIS percibido en compras”* coloque el monto del ITBIS percibido por
    terceros al momento de la facturación de las operaciones.
    *Este campo no estará habilitado hasta tanto no existan normativas que establezcan un
    régimen de percepción u obliguen a los contribuyentes a realizar la misma.
    """

    return ""


def _has_retencion_isr(
    invoice_id=None, from_date=None, to_date=None, company=None
) -> bool:
    """Retención ISR

    En “Retención ISR” registre el monto de la retención del Impuesto Sobre la Renta
    (ISR) que le fue aplicada a la factura. Este campo no estará habilitado hasta tanto
    no existan normativas que establezcan un régimen de retención u obliguen a los
    contribuyentes a realizar la misma.
    """

    return bool(
        get_isr_retenido(
            invoice_id=invoice_id, from_date=from_date, to_date=to_date, company=company
        ) > 0.0
    )
    

def get_tipo_retencion_isr(
    invoice_id=None, from_date=None, to_date=None, company=None
) -> Union[float, str]:
    """Tipo de Retención ISR

    En “Tipo de Retención ISR” registre el tipo de retención que le fue aplicado a la
    factura. Este campo no estará habilitado hasta tanto no existan normativas que
    establezcan un régimen de retención u obliguen a los contribuyentes a realizar la
    misma.
    """

    # retention_map = {
    #     "1. Alquileres": 1,
    #     "2. Honorarios por servicios": 2,
    #     "3. Otras rentas": 3,
    #     "4. Otras rentas (rentas presuntas)": 4,
    #     "5. Intereses pagados a personas jurídicas residentes": 5,
    #     "6. Intereses pagados a personas físicas residentes": 6,
    #     "7. Retención por proveedor": 7,
    # }

    if _has_retencion_isr(
        invoice_id=invoice_id, from_date=from_date, to_date=to_date, company=company
    ):
        return 2

    return ""


isr_retenido = None


def get_isr_retenido(
    invoice_id=None, from_date=None, to_date=None, company=None
) -> Union[float, str]:
    """Monto Retención Renta

    En “Monto Retención Renta” digite el monto del Impuesto Sobre la Renta
    retenido producto de la prestación o locación de servicios. Es el resultado de
    multiplicar el monto del campo “Servicios” por el porcentaje de la retención según
    corresponda. Siempre que se llene este campo, debe haber completado la casilla 7
    (fecha pago).
    """


    # either invoice_id or (from_date and to_date) must be provided
    if not invoice_id and (not from_date or not to_date):
        frappe.throw(
            "Either invoice_id or (from_date and to_date and company) must be provided"
        )

    def generator():
        company_filter = str()
        if company:
            company_filter = f"And parent.company = {company!r}"

        return dict(
            frappe.db.sql(
                f"""
                    Select
                        parent.name As invoice_id,
                        Sum(-child.base_tax_amount) As amount
                    From
                        `tabPurchase Taxes and Charges` As  child
                    Inner Join
                        `tabPurchase Invoice` As  parent
                        On
                            child.parenttype = "Purchase Invoice"
                            And child.parentfield = "taxes"
                            And child.parent = parent.name
                            And child.docstatus = parent.docstatus
                            And child.dominican_tax_type = "ISR"
                            And child.add_deduct_tax = "Deduct"
                    Where
                        parent.docstatus = 1
                        {company_filter}
                        And parent.posting_date Between {from_date!r} And {to_date!r}
                        And parent.is_opening = "No"
                    Group by
                        parent.name
                """
            )
        )

    global isr_retenido
    if isr_retenido is None:
        isr_retenido = generator()
    
    return isr_retenido.get(invoice_id, 0.0) if invoice_id else sum(isr_retenido.values())

def get_isr_percibido(
    invoice_id=None, from_date=None, to_date=None, company=None
) -> Union[float, str]:
    """ISR Percibido en compras

    En “ISR percibido en compras”* coloque el monto del ISR percibido por terceros al
    momento de la facturación de las operaciones.
    *Este campo no estará habilitado hasta tanto no existan normativas que establezcan un
    régimen de percepción u obliguen a los contribuyentes a realizar la misma.
    """

    return ""


selectivo_facturado = None


def get_selectivo_facturado(
    invoice_id=None, from_date=None, to_date=None, company=None
) -> float:
    """Impuesto Selectivo al Consumo
    
    En “Impuesto Selectivo al Consumo” indique el monto correspondiente al
    Impuesto Selectivo al Consumo producto de una compra gravada con este impuesto
    (si aplica).
    """

    # either invoice_id or (from_date and to_date) must be provided
    if not invoice_id and (not from_date or not to_date):
        frappe.throw(
            "Either invoice_id or (from_date and to_date and company) must be provided"
        )

    def generator():
        company_filter = str()
        if company:
            company_filter = f"And parent.company = {company!r}"

        return dict(
            frappe.db.sql(
                f"""
                    Select
                        parent.name As invoice_id,
                        Sum(child.base_tax_amount) As amount
                    From
                        `tabPurchase Taxes and Charges` As  child
                    Inner Join
                        `tabPurchase Invoice` As  parent
                        On
                            child.parenttype = "Purchase Invoice"
                            And child.parentfield = "taxes"
                            And child.parent = parent.name
                            And child.docstatus = parent.docstatus
                            And child.dominican_tax_type = "ISC"
                            And child.add_deduct_tax = "Add"
                    Where
                        parent.docstatus = 1
                        {company_filter}
                        And parent.posting_date Between {from_date!r} And {to_date!r}
                        And parent.is_opening = "No"
                    Group by
                        parent.name
                """
            )
        )

    global selectivo_facturado
    if selectivo_facturado is None:
        selectivo_facturado = generator()
    
    return selectivo_facturado.get(invoice_id, 0.0) if invoice_id else sum(selectivo_facturado.values())


otros_impuestos = None


def get_otros_imp_facturado(
    invoice_id=None, from_date=None, to_date=None, company=None
) -> float:
    """Otros Impuestos/Tasas

    En “Otros Impuestos/Tasas” digite cualquier otro impuesto o tasa no
    especificado en el Formato de Envío y que formen parte del valor del comprobante
    fiscal.
    """

    # either invoice_id or (from_date and to_date) must be provided
    if not invoice_id and (not from_date or not to_date):
        frappe.throw(
            "Either invoice_id or (from_date and to_date and company) must be provided"
        )

    def generator():
        company_filter = str()
        if company:
            company_filter = f"And parent.company = {company!r}"

        return dict(
            frappe.db.sql(
                f"""
                    Select
                        parent.name As invoice_id,
                        Sum(child.base_tax_amount) As amount
                    From
                        `tabPurchase Taxes and Charges` As  child
                    Inner Join
                        `tabPurchase Invoice` As  parent
                        On
                            child.parenttype = "Purchase Invoice"
                            And child.parentfield = "taxes"
                            And child.parent = parent.name
                            And child.docstatus = parent.docstatus
                            And child.dominican_tax_type Not In ("ISC", "ITBIS", "ISR", "LEGAL TIP")
                            And child.add_deduct_tax = "Add"
                    Where
                        parent.docstatus = 1
                        {company_filter}
                        And parent.posting_date Between {from_date!r} And {to_date!r}
                        And parent.is_opening = "No"
                    Group by
                        parent.name
                """
            )
        )

    global otros_impuestos
    if otros_impuestos is None:
        otros_impuestos = generator()
    
    return otros_impuestos.get(invoice_id, 0.0) if invoice_id else sum(otros_impuestos.values())


propina_legal = None


def get_propina_facturada(
    invoice_id=None, from_date=None, to_date=None, company=None
) -> float:
    """Monto Propina Legal
    
    En “Monto Propina Legal” coloque el monto de la propina establecida por la
    Ley No. 54-32 (10%).
    """

    # either invoice_id or (from_date and to_date) must be provided
    if not invoice_id and (not from_date or not to_date):
        frappe.throw(
            "Either invoice_id or (from_date and to_date and company) must be provided"
        )

    def generator():
        company_filter = str()
        if company:
            company_filter = f"And parent.company = {company!r}"

        return dict(
            frappe.db.sql(
                f"""
                    Select
                        parent.name As invoice_id,
                        Sum(child.base_tax_amount) As amount
                    From
                        `tabPurchase Taxes and Charges` As  child
                    Inner Join
                        `tabPurchase Invoice` As  parent
                        On
                            child.parenttype = "Purchase Invoice"
                            And child.parentfield = "taxes"
                            And child.parent = parent.name
                            And child.docstatus = parent.docstatus
                            And child.dominican_tax_type = "LEGAL TIP"
                            And child.add_deduct_tax = "Add"
                    Where
                        parent.docstatus = 1
                        {company_filter}
                        And parent.posting_date Between {from_date!r} And {to_date!r}
                        And parent.is_opening = "No"
                    Group by
                        parent.name
                """
            )
        )

    global propina_legal
    if propina_legal is None:
        propina_legal = generator()
    
    return propina_legal.get(invoice_id, 0.0) if invoice_id else sum(propina_legal.values())


mode_of_payment = None


def get_forma_de_pago(
    invoice_id=None, from_date=None, to_date=None, company=None
) -> str:
    """Forma de Pago

    En “Forma de Pago” registre la forma de pago utilizada para la transacción.
    """

    payment_mode_map = {
        "1. Efectivo": 1,
        "2. Cheques / Transferencias / Depósito": 2,
        "3. Tarjeta de Crédito / Débito": 3,
        "4. Compra a Crédito": 4,
        "5. Permuta": 5,
        "6. Notas de Crédito (no usar)": 6,
        "7. Mixto (no usar)": 7,
    }

    # read through the payment entries and categorize each invoice
    def generator():
        company_filter = str()
        if company:
            company_filter = f"And parent.company = {company!r}"

        return dict(
            frappe.db.sql(
                f"""
                    Select
                        invoice_id,
                        Case 
                            When Count(DISTINCT dgii_mode_of_payment) = 1 Then Max(dgii_mode_of_payment)
                            Else '7. Mixto (no usar)'
                        End As payment_mode
                    From (
                        Select
                            child.reference_name As invoice_id,
                            mode.dgii_mode_of_payment
                        From
                            `tabPayment Entry Reference` As  child
                        Inner Join
                            `tabPayment Entry` As  parent
                            On
                                child.parenttype = "Payment Entry"
                                And child.parentfield = "references"
                                And child.parent = parent.name
                                And child.docstatus = parent.docstatus
                                And child.reference_doctype = "Purchase Invoice"
                        Inner Join
                            `tabMode of Payment` As mode
                            On parent.mode_of_payment = mode.name
                        Inner Join
                            `tabPurchase Invoice` As  invoice
                            On 
                                child.reference_name = invoice.name
                                And child.reference_doctype = "Purchase Invoice"
                                And child.docstatus = invoice.docstatus
                        Where
                            parent.docstatus = 1
                            {company_filter}
                            And invoice.is_opening = "No"
                            And invoice.posting_date Between {from_date!r} And {to_date!r}
                       

                    Union All

                        Select
                            parent.name As invoice_id,
                            mode.dgii_mode_of_payment As dgii_mode_of_payment
                        From
                            `tabPurchase Invoice` As  parent
                        Inner Join
                            `tabMode of Payment` As mode
                            On parent.mode_of_payment = mode.name
                        Where
                            parent.docstatus = 1
                            {company_filter}
                            And parent.is_opening = "No"
                            And parent.mode_of_payment Is Not Null
                            And parent.posting_date Between {from_date!r} And {to_date!r}
                    
                    Union All

                        Select
                            invoice.name As invoice_id,
                            mode.dgii_mode_of_payment As dgii_mode_of_payment
                        From
                            `tabJournal Entry` As  parent
                        Inner Join
                            `tabJournal Entry Account` As  child
                            On
                                child.parenttype = "Journal Entry"
                                And child.parentfield = "accounts"
                                And child.parent = parent.name
                                And child.docstatus = parent.docstatus
                                And child.reference_type = "Purchase Invoice"
                        Inner Join
                            `tabMode of Payment` As mode
                            On parent.mode_of_payment = mode.name
                        Inner Join
                            `tabPurchase Invoice` As invoice
                            On
                                child.reference_name = invoice.name
                                And child.reference_type = "Purchase Invoice"
                                And child.docstatus = invoice.docstatus
                        Where
                            parent.docstatus = 1
                            {company_filter}
                            And parent.is_opening = "No"
                            And invoice.posting_date Between {from_date!r} And {to_date!r}
                    ) As temp
                Where
                    invoice_id Is Not Null
                Group By
                    invoice_id
                """
            )
        )
    
    global mode_of_payment
    if mode_of_payment is None:
        mode_of_payment = generator()
    
    try:
        return payment_mode_map[
            mode_of_payment.get(invoice_id, "4. Compra a Crédito") if invoice_id else mode_of_payment
        ]
    except KeyError:
        frappe.throw(
            f"Invalid payment mode for invoice {invoice_id}: {mode_of_payment.get(invoice_id, 4)}"
        )
    return 4
