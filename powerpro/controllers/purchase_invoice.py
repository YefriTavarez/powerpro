# Copyright (c) 2024, Rainier J  Polanco and Contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cint

def validate(doc, event):
	set_taxes(doc)
	calculate_totals(doc)
	validate_duplicate_ncf(doc)
	valid_prefix(doc)
	validate_rnc(doc)
	validate_retention_type(doc)

def before_submit(doc, event):
	generate_new(doc)

def calculate_totals(doc):
	total_bienes = total_servicios = .000

	for item in doc.items:
		if item.item_type == "Bienes":
			total_bienes += item.base_amount
		
		if item.item_type == "Servicios":
			total_servicios += item.base_amount
	
	doc.monto_facturado_bienes = total_bienes
	doc.monto_facturado_servicios = total_servicios
	
def generate_new(doc):
	tax_category = frappe.db.get_value(
		"Supplier",
		doc.supplier,
		"tax_category"
	)
	if doc.ncf or not tax_category:
		return

	ncf_serie = get_serie_for_(doc)

	current = cint(ncf_serie.current)

	if cint(ncf_serie.top) and current >= cint(ncf_serie.top):
		frappe.throw(
			"Ha llegado al máximo establecido para esta serie de comprobantes!")

	current += 1

	ncf_serie.current = current
	ncf_serie.db_update()

	doc.ncf = '{0}{1:08d}'.format(ncf_serie.serie.split(".")[0], current)
	doc.vencimiento_ncf = ncf_serie.expiration
	doc.db_update()
	frappe.db.commit()


def get_serie_for_(doc):
	supplier_category = frappe.get_value("Supplier", doc.supplier, "tax_category")
	if not supplier_category:
		frappe.throw(
			"""Favor seleccionar una categoría de impuestos para el 
			suplidor <a href='/desk#Form/Supplier/{0}'>{0}</a>""".format(doc.supplier_name)
		)
	
	filters = {
		"company": doc.company,
		"tax_category": supplier_category,
		# "serie": "B11.##########"
	}
	if not frappe.db.exists("NCF Manager", filters):
		frappe.throw("No existe una secuencia de NCF para el tipo {}".format(supplier_category))

	return frappe.get_doc("NCF Manager", filters)

def set_taxes(doc):	
	dgi_setting = frappe.get_single(
		"DGII Settings"
	)

	total_tip = total_excise = .000

	if dgi_setting.multi_company:
		for row in dgi_setting.multi_company:
			if row.company == doc.company:
				total_tip = sum(
					tax.base_tax_amount_after_discount_amount for tax in doc.taxes if tax.account_head == row.itbis_account
				)
				doc.total_itbis = total_tip

				total_tip = sum(
					tax.base_tax_amount_after_discount_amount for tax in doc.taxes if tax.account_head == row.legal_tip_account
				)
				doc.legal_tip = total_tip

				total_excise = sum(
					tax.base_tax_amount_after_discount_amount for tax in doc.taxes if tax.account_head == row.excise_tax
				)
				doc.excise_tax = total_excise

				return


	if dgi_setting.itbis_account:
		total_tip = sum( 
			[ row.base_tax_amount_after_discount_amount for row in filter(
					lambda x: x.account_head == dgi_setting.itbis_account,
					doc.taxes
				)
			]

		)
		doc.total_itbis = total_tip

	if dgi_setting.legal_tip_account:
		total_tip = sum( 
			[ row.base_tax_amount_after_discount_amount for row in filter(
					lambda x: x.account_head == dgi_setting.legal_tip_account,
					doc.taxes
				)
			]

		)
		doc.legal_tip = total_tip
		
	if dgi_setting.excise_tax:
		total_excise = sum( 
			[ row.base_tax_amount_after_discount_amount for row in filter(
					lambda x: x.account_head == dgi_setting.excise_tax,
					doc.taxes
				)
			]

		)
		doc.excise_tax = total_excise
		
	
	if dgi_setting.other_tax_detail:
		for tax in dgi_setting.other_tax_detail:
			total_amount = .000
			total_amount = sum(
				[ row.base_tax_amount_after_discount_amount for row in filter(
						lambda x: x.account_head == tax.account,
						doc.taxes
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
		frappe.throw("""
			Ya existe una factura registrada a nombre de <b>{supplier_name}</b> 
			con el mismo NCF <b>{ncf}</b>, favor verificar!
		""".format(**doc.as_dict()))

def validate_retention_type(doc):
	conf = frappe.get_doc("DGII Settings")
	# if not hasattr(conf, "dgii_settings_multi_company"):
	# 	return
	
	matched_other_rows = list(
		filter(
			lambda x, 
			comp = doc.company: x.company == comp and x.tax_type == "itbis_retenido", 
			conf.multi_other_tax_detail
		)
	)

	matched_accounts = set(
		[ t.account_head for t in doc.taxes]
	).intersection(
		[ d.account for d in matched_other_rows ]
	)
	
	if not matched_accounts and doc.include_retention:
		frappe.throw("Marcaste la casilla de incluir retención de ITBIS, pero no se encontró una cuenta de retención de ITBIS configurada para esta empresa")
	if matched_accounts and not doc.include_retention:
		frappe.throw(f"""
			No marcaste la casilla de incluir retención de ITBIS, pero se encontraron cuentas de retención de ITBIS configuradas para esta empresa.
			   <br><ul>{'<li>{}</li>'.join(matched_accounts)}</ul>
		""")
	
	doc.itbis_retenido = sum(
		[ tax.base_tax_amount_after_discount_amount for tax in doc.taxes if tax.account_head in matched_accounts ]
	)

	# frappe.msgprint(f"matched_accounts: {matched_accounts}")
	# frappe.msgprint(f"itbis_retenido: {doc.itbis_retenido}")

def valid_prefix(doc):
	ncf_quantity = 0
	ncf_quantity = len(doc.ncf)
	valid_prefix = ["B01", "B02", "B04", "B11", "B13", "B14", "B15", "E31", "E33", "E34"]
	if ncf_quantity != 11 and ncf_quantity != 13:
		frappe.throw(f'El numero de comprobante tiene <b>{ncf_quantity}</b> caracteres, deben ser <b>11</b> o <b>13</b> para la serie E.')
	
	if not doc.ncf[:3] in valid_prefix:
		frappe.throw(f'El prefijo <b>{doc.ncf[:3]}</b> no es valido, favor verificar!')

def validate_rnc(doc):
	if not doc.tax_id:
		return

	len_tax_id = len(doc.tax_id)

	if len_tax_id == 9 or len_tax_id == 11:
		return

	frappe.throw("El RNC/Cédula debe tener 9 o 11 caracteres")