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
			console.log({ dont_refresh})
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
}