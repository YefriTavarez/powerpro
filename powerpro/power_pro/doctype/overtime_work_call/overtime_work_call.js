// Copyright (c) 2026, PowerPro contributors

frappe.ui.form.on("Overtime Work Call", {
	setup(frm) {
		frm.set_query("employee", "employees", () => ({
			filters: {
				company: frm.doc.company,
				status: "Active",
				overtime_eligible: 1,
			},
		}));
	},

	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.dashboard.set_headline_alert(
				__("Submitting this call immediately authorizes the generated employee/date overtime windows."),
				"blue"
			);
			frm.add_custom_button(__("Generate Dates"), () => generate_dates(frm), __("Schedule"));
			frm.add_custom_button(__("Add Eligible Employees"), () => add_employees(frm), __("Employees"));
		}

		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__("Refresh Actual Attendance"), () => preview_reconciliation(frm), __("Overtime"));
			frm.add_custom_button(__("View Individual Authorizations"), () => {
				frappe.set_route("List", "Overtime Authorization", {
					overtime_work_call: frm.doc.name,
				});
			}, __("Overtime"));
			frm.add_custom_button(__("Preview and Settle Team"), () => {
				if (frm.doc.planned_settlement === "Cash") {
					show_team_payroll_date_dialog(frm);
					return;
				}
				preview_team_settlement(frm, null);
			}, __("Settlement"));
		}
	},

	from_date(frm) {
		if (!frm.doc.to_date) frm.set_value("to_date", frm.doc.from_date);
	},

	default_start_time(frm) {
		apply_default_times(frm);
	},

	default_end_time(frm) {
		apply_default_times(frm);
	},
});

frappe.ui.form.on("Overtime Work Call Date", {
	work_date(frm, cdt, cdn) {
		set_requested_hours(cdt, cdn);
	},
	start_time(frm, cdt, cdn) {
		set_requested_hours(cdt, cdn);
	},
	end_time(frm, cdt, cdn) {
		set_requested_hours(cdt, cdn);
	},
});

function generate_dates(frm) {
	if (!frm.doc.from_date || !frm.doc.to_date || !frm.doc.default_start_time || !frm.doc.default_end_time) {
		frappe.msgprint(__("Enter From Date, To Date, Team Start Time, and Team End Time first."));
		return;
	}
	if (frappe.datetime.get_diff(frm.doc.to_date, frm.doc.from_date) < 0) {
		frappe.msgprint(__("To Date must be on or after From Date."));
		return;
	}
	if (frappe.datetime.get_diff(frm.doc.to_date, frm.doc.from_date) > 365) {
		frappe.msgprint(__("One overtime work call is limited to 366 requested dates."));
		return;
	}

	const add_rows = () => {
		frm.clear_table("dates");
		let work_date = frm.doc.from_date;
		while (frappe.datetime.get_diff(frm.doc.to_date, work_date) >= 0) {
			const row = frm.add_child("dates", {
				work_date,
				start_time: frm.doc.default_start_time,
				end_time: frm.doc.default_end_time,
			});
			row.requested_hours = hours_between(row.start_time, row.end_time);
			work_date = frappe.datetime.add_days(work_date, 1);
		}
		frm.refresh_field("dates");
	};

	if (frm.doc.dates?.length) {
		frappe.confirm(__("Replace the existing requested date rows with this range?"), add_rows);
	} else {
		add_rows();
	}
}

function apply_default_times(frm) {
	(frm.doc.dates || []).forEach((row) => {
		if (frm.doc.default_start_time) row.start_time = frm.doc.default_start_time;
		if (frm.doc.default_end_time) row.end_time = frm.doc.default_end_time;
		row.requested_hours = hours_between(row.start_time, row.end_time);
	});
	frm.refresh_field("dates");
}

function add_employees(frm) {
	if (!frm.doc.company) {
		frappe.msgprint(__("Select the Company first."));
		return;
	}
	const dialog = new frappe.ui.form.MultiSelectDialog({
		doctype: "Employee",
		target: frm,
		setters: {
			company: frm.doc.company,
			department: frm.doc.department || null,
		},
		add_filters_group: 1,
		get_query() {
			const filters = {
				company: frm.doc.company,
				status: "Active",
				overtime_eligible: 1,
			};
			if (frm.doc.department) filters.department = frm.doc.department;
			return {
				filters,
			};
		},
		action(selections) {
			const existing = new Set((frm.doc.employees || []).map((row) => row.employee));
			(selections || []).forEach((employee) => {
				if (!existing.has(employee)) {
					frm.add_child("employees", { employee });
					existing.add(employee);
				}
			});
			frm.refresh_field("employees");
			dialog.dialog.hide();
		},
	});
}

function set_requested_hours(cdt, cdn) {
	const row = locals[cdt][cdn];
	frappe.model.set_value(cdt, cdn, "requested_hours", hours_between(row.start_time, row.end_time));
}

function hours_between(start, end) {
	if (!start || !end) return 0;
	const seconds = (value) => {
		const parts = String(value).split(":").map(Number);
		return (parts[0] || 0) * 3600 + (parts[1] || 0) * 60 + (parts[2] || 0);
	};
	let duration = seconds(end) - seconds(start);
	if (duration <= 0) duration += 24 * 3600;
	return flt(duration / 3600, 4);
}

function preview_reconciliation(frm) {
	frappe.call({
		method: "powerpro.power_pro.doctype.overtime_work_call.overtime_work_call.reconcile_overtime_work_call",
		args: { work_call: frm.doc.name, dry_run: 1 },
		freeze: true,
		freeze_message: __("Comparing requested windows with Employee Checkins..."),
	}).then(({ message }) => {
		const result = message || {};
		const body = (result.rows || []).map((row) => `
			<tr>
				<td>${escape_html(row.employee_name || row.employee)}</td>
				<td>${escape_html(row.work_date)}</td>
				<td class="text-right">${format_number(row.requested_hours)}</td>
				<td class="text-right">${format_number(row.verified_hours)}</td>
				<td class="text-right">${format_number(row.adherence_percent)}%</td>
				<td>${escape_html(__(row.reconciliation_status))}</td>
			</tr>`).join("");
		const summary = `
			<p><strong>${__("Requested hours")}:</strong> ${format_number(result.requested_hours)} &nbsp;
			<strong>${__("Verified hours")}:</strong> ${format_number(result.verified_hours)} &nbsp;
			<strong>${__("Adherence")}:</strong> ${format_number(result.adherence_percent)}%</p>
			<div class="table-responsive"><table class="table table-bordered">
			<thead><tr><th>${__("Employee")}</th><th>${__("Work Date")}</th><th>${__("Requested")}</th><th>${__("Verified")}</th><th>${__("Adherence")}</th><th>${__("Status")}</th></tr></thead>
			<tbody>${body}</tbody></table></div>`;
		const options = {
			title: __("Overtime Reconciliation Preview"),
			message: summary,
			wide: true,
		};
		if ((result.rows || []).some((row) => row.reconciliation_status !== "Scheduled")) {
			options.primary_action = {
				label: __("Save Attendance Snapshot"),
				action() {
					dialog.hide();
					save_reconciliation(frm);
				},
			};
		}
		const dialog = frappe.msgprint(options);
	});
}

function save_reconciliation(frm) {
	frappe.call({
		method: "powerpro.power_pro.doctype.overtime_work_call.overtime_work_call.reconcile_overtime_work_call",
		args: { work_call: frm.doc.name, dry_run: 0 },
		freeze: true,
		freeze_message: __("Saving verified attendance and adherence..."),
	}).then(({ message }) => {
		frappe.show_alert({
			message: __("Reconciled {0} individual authorizations.", [message.authorization_count]),
			indicator: message.work_call_status === "Completed" ? "green" : "orange",
		});
		frm.reload_doc();
	});
}

function show_team_payroll_date_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Team Cash Settlement Payroll Date"),
		fields: [{
			fieldname: "payroll_date",
			fieldtype: "Date",
			label: __("Payroll Date"),
			reqd: 1,
			default: frappe.datetime.get_today(),
		}],
		primary_action_label: __("Preview"),
		primary_action(values) {
			dialog.hide();
			preview_team_settlement(frm, values.payroll_date);
		},
	});
	dialog.show();
}

function preview_team_settlement(frm, payroll_date) {
	frappe.call({
		method: "powerpro.controllers.overtime_settlement.preview_overtime_work_call_settlement",
		args: { work_call: frm.doc.name, payroll_date },
		freeze: true,
		freeze_message: __("Calculating every employee settlement..."),
	}).then(({ message }) => show_team_settlement_preview(frm, message, payroll_date));
}

function show_team_settlement_preview(frm, result, payroll_date) {
	const is_cash = result.method === "Cash";
	const rows = (result.rows || []).map((row) => `
		<tr>
			<td>${escape_html(row.employee_name || row.employee)}</td>
			<td>${escape_html(row.work_date)}</td>
			<td class="text-right">${format_number(row.verified_hours || row.current_hours)}</td>
			<td class="text-right">${is_cash
				? escape_html(format_currency(row.total_amount, row.currency))
				: format_number(row.days_to_credit)}</td>
		</tr>`).join("");
	const summary_value = is_cash
		? format_currency(result.total_amount, result.currency)
		: format_number(result.leave_days_to_credit);
	let dialog;
	dialog = frappe.msgprint({
		title: __("Team Overtime Settlement Preview"),
		message: `<p><strong>${__("Authorizations")}:</strong> ${result.authorization_count} &nbsp;
			<strong>${is_cash ? __("Total Amount") : __("Leave Days Added")}:</strong> ${escape_html(summary_value)}</p>
			<div class="table-responsive"><table class="table table-bordered">
			<thead><tr><th>${__("Employee")}</th><th>${__("Work Date")}</th><th>${__("Hours")}</th><th>${is_cash ? __("Amount") : __("Leave Days")}</th></tr></thead>
			<tbody>${rows}</tbody></table></div>
			<p class="text-muted">${__("Nothing has been created yet. The confirmation is atomic for the complete team.")}</p>`,
		wide: true,
		primary_action: {
			label: is_cash ? __("Create Team Additional Salaries") : __("Credit Team Compensatory Rest"),
			action() {
				dialog.hide();
				frappe.call({
					method: "powerpro.controllers.overtime_settlement.settle_overtime_work_call",
					args: { work_call: frm.doc.name, payroll_date },
					freeze: true,
					freeze_message: __("Creating the audited team settlement..."),
				}).then(() => frm.reload_doc());
			},
		},
	});
}

function escape_html(value) {
	return frappe.utils.escape_html(String(value ?? ""));
}

function format_number(value) {
	return format_number_for_grid(flt(value || 0, 2));
}

function format_number_for_grid(value) {
	return Number(value || 0).toFixed(2);
}
