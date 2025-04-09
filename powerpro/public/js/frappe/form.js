// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

{
	// Override to add dont_refresh parameter to call
	// to prevent refreshing the form after a call
	// This is useful for calls that are made in the background
	// and don't require a refresh
	// Example: frappe.call("method", { args }, callback, true);
	// This will prevent the form from refreshing after the call
	// and will allow the callback to be executed without refreshing
	// the form.
	//
	const { Form } = frappe.ui.form;
	Form
		.prototype
		.call = function (opts, args, callback, dont_refresh) {
			var me = this;
			if (typeof opts === "string") {
				// called as frm.call('do_this', {with_arg: 'arg'});
				opts = {
					method: opts,
					doc: this.doc,
					args: args,
					callback: callback,
				};
			}
			if (!opts.doc) {
				if (opts.method.indexOf(".") === -1)
					opts.method = frappe.model.get_server_module_name(me.doctype) + "." + opts.method;
				opts.original_callback = opts.callback;
				opts.callback = function (r) {
					if ($.isPlainObject(r.message)) {
						if (opts.child) {
							// update child doc
							opts.child = locals[opts.child.doctype][opts.child.name];
							// if child row is deleted, don't update
							if (opts.child) {
								var std_field_list = ["doctype"]
									.concat(frappe.model.std_fields_list)
									.concat(frappe.model.child_table_field_list);
								for (var key in r.message) {
									if (std_field_list.indexOf(key) === -1) {
										opts.child[key] = r.message[key];
									}
								}

								me.fields_dict[opts.child.parentfield].refresh();
							}
						} else {
							// update parent doc
							me.set_value(r.message);
						}
					}
					opts.original_callback && opts.original_callback(r);
				};
			} else {
				opts.original_callback = opts.callback;
				opts.callback = function (r) {
					if (!r.exc && !dont_refresh) {
						me.refresh_fields();
					}

					opts.original_callback && opts.original_callback(r);
				};
			}
			return frappe.call(opts);
		};

	Form
		.prototype
		.setup_file_drop = function() {
			var me = this;
			this.$wrapper.on("dragenter dragover", false).on("drop", function (e) {
				var dataTransfer = e.originalEvent.dataTransfer;
				if (!(dataTransfer && dataTransfer.files && dataTransfer.files.length > 0)) {
					return;
				}
	
				e.stopPropagation();
				e.preventDefault();
	
				if (me.doc.__islocal) {
					frappe.msgprint(__("Please save before attaching."));
					throw "attach error";
				}

				const files = dataTransfer.files;
				if (files.length > 1) {
					frappe.msgprint(__("You can only attach one file at a time."));
					throw "attach error";
				}
				if (files.length === 0) {
					frappe.msgprint(__("Please select a file to attach."));
					throw "attach error";
				}
				if (files[0].size > 104857600) {
					frappe.msgprint(__("File size exceeds 100 MB."));
					throw "attach error";
				}
				if (files[0].size === 0) {
					frappe.msgprint(__("File size cannot be zero."));
					throw "attach error";
				}
				if (files[0].type === "") {
					frappe.msgprint(__("File type cannot be empty."));
					throw "attach error";
				}
	
				powerpro.utils.select_attachment_type(
					me.doctype, me.docname, function (attachment_type) {
						return new frappe.ui.powerFileUploader({
							doctype: me.doctype,
							docname: me.docname,
							attachment_type: attachment_type,
							frm: me,
							files: files,
							folder: "Home/Attachments",
							on_success(file_doc) {
								me.attachments.attachment_uploaded(file_doc);
							},
						});
					}
				)
			});
		}
}