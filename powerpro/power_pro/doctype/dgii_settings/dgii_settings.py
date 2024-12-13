# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class DGIISettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from powerpro.power_pro.doctype.dgii_settings_multi_company.dgii_settings_multi_company import DGIISettingsMultiCompany
		from powerpro.power_pro.doctype.multi_other_tax_detail.multi_other_tax_detail import MultiOtherTaxDetail
		from powerpro.power_pro.doctype.other_tax_detail.other_tax_detail import OtherTaxDetail

		excise_tax: DF.Link | None
		itbis_account: DF.Link | None
		legal_tip_account: DF.Link | None
		multi_company: DF.Table[DGIISettingsMultiCompany]
		multi_other_tax_detail: DF.Table[MultiOtherTaxDetail]
		non_formal_tax_category: DF.Link | None
		other_tax_detail: DF.Table[OtherTaxDetail]
	# end: auto-generated types
	pass
