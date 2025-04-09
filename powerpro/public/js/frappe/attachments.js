// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

{
    const { Attachments } = frappe.ui.form;

    const { new_attachment: original } = Attachments.prototype;
    Attachments.prototype.new_attachment = function(fieldname) {
		const self = this;

		if (self.dialog) {
			// remove upload dialog
			self.dialog.$wrapper.remove();
		}

		const restrictions = {};
		if (self.frm.meta.max_attachments) {
			restrictions.max_number_of_files =
				self.frm.meta.max_attachments - self.frm.attachments.get_attachments().length;
		}

		powerpro.utils.select_attachment_type(
			self.frm.doctype, self.frm.docname, function(attachment_type) {

			return new frappe.ui.powerFileUploader({
				doctype: self.frm.doctype,
				docname: self.frm.docname,
				attachment_type: attachment_type,
				frm: self.frm,
				folder: "Home/Attachments",
				on_success: (file_doc) => {
					self.attachment_uploaded(file_doc);
				},
				restrictions,
				make_attachments_public: self.frm.meta.make_attachments_public,
			});
		});
	};
}