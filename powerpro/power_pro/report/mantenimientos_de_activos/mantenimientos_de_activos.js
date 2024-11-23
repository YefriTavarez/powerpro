// Copyright (c) 2024, Miguel Higuera and contributors
// For license information, please see license.txt

frappe.query_reports["Mantenimientos de Activos"] = {
    "filters": [
        {
            "label": __("From Date"),
            "fieldname": "from_date",
            "fieldtype": "Date",
            "default": frappe.datetime.year_start(),
            "reqd": 1,
        },
        {
            "label": __("To Date"),
            "fieldname": "to_date",
            "fieldtype": "Date",
            "default": frappe.datetime.year_end(),
            "reqd": 1,
        },
        {
            "label": __("Asset Maintenance"),
            "fieldname": "asset_maintenance",
            "fieldtype": "Link",
            "options": "Asset Maintenance",
        },
        {
            "label": __("Asset"),
            "fieldname": "asset",
            "fieldtype": "Link",
            "options": "Asset",
        },
        {
            "label": __("Maintenance Team"),
            "fieldname": "maintenance_team",
            "fieldtype": "Link",
            "options": "Asset Maintenance Team",
        },
        {
            "label": __("Maintenance Status"),
            "fieldname": "maintenance_status",
            "fieldtype": "Select",
            "options": [
                "",
                "Planned",
                "Completed",
                "Overdue",
                "Cancelled",
            ]
        },
        {
            "label": __("Periodicity"),
            "fieldname": "periodicity",
            "fieldtype": "Select",
            "options": [
                "",
                "Daily",
                "Weekly",
                "Monthly",
                "Quarterly",
                "Half-yearly",
                "Yearly",
                "2 Yearly",
                "3 Yearly",
            ]
        },
        {
            "label": __("Summary"),
            "fieldname": "summary",
            "fieldtype": "Check",
            "default": 1,
        },
    ]
};
