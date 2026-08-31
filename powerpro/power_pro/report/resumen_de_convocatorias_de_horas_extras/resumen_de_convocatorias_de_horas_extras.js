// Copyright (c) 2026, PowerPro contributors

frappe.query_reports["Resumen de Convocatorias de Horas Extras"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
			reqd: 1,
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
			get_query: () => ({
				filters: {
					company: frappe.query_report.get_filter_value("company"),
					status: "Active",
				},
			}),
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		},
		{
			fieldname: "reconciliation_status",
			label: __("Reconciliation Status"),
			fieldtype: "Select",
			options: ["", "Scheduled", "Completed", "Partial", "Absent", "Overrun", "Check-in Issue"],
		},
	],
};
