# Copyright (c) 2024, Miguel Higuera and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, cint, flt, formatdate, format_datetime
from frappe.model.document import Document
from frappe.utils.csvutils import UnicodeWriter
import time


class Reporte608(Document):
	pass


@frappe.whitelist()
def get_file_address(from_date, to_date):
	data = f"""
		Select 
			ncf, 
			posting_date, 
			cancellation_type
		From 
			`tabSales Invoice` 
		Where 
			docstatus = 2 And
			informal_customer = 0 And
			posting_date Between {from_date!r} And {to_date!r}
		"""
	result = frappe.db.sql(data, as_dict=True)

	w = UnicodeWriter()
	w.writerow([
		"Numero de Comprobante Fiscal",
		"Fecha de Comprobante",
		"Tipo de Anulacion",
		"Estatus"
	])

	for row in result:
		#bill_no = row.bill_no.split("-")[1] if(len(row.bill_no.split("-")) > 1) else row.bill_no # NCF-A1##% || A1##%
		year  = str(row.posting_date).split("-")[0]
		month  = str(row.posting_date).split("-")[1]
		date  = str(row.posting_date).split("-")[2]

		w.writerow([
			row.ncf,
			year + month + date,
			row.cancellation_type,
			"",
		])

	frappe.response['result'] = cstr(w.getvalue())
	frappe.response['type'] = 'csv'
	frappe.response['doctype'] = "Reporte_608_" + str(int(time.time()))