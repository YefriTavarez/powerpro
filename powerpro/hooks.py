app_name = "powerpro"
app_title = "Power Pro"
app_publisher = "Yefri Tavarez"
app_description = "Manufacturing Powered"
app_email = "yefritavarez@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "powerpro",
# 		"logo": "/assets/powerpro/logo.png",
# 		"title": "Power Pro",
# 		"route": "/powerpro",
# 		"has_permission": "powerpro.api.permission.has_app_permission"
# 	}
# ]

# Fixtures
# --------

fixtures = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/powerpro/css/powerpro.css"
app_include_js = [
    "/assets/powerpro/js/powerpro.js?v=1.0.1",
    "/assets/powerpro/js/frappe/indicator.js?v=1.0.1",
    "app.bundle.js",
]

# include js, css files in header of web template
# web_include_css = "/assets/powerpro/css/powerpro.css"
# web_include_js = "/assets/powerpro/js/powerpro.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "powerpro/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Item" : "public/js/item.js",
    "Salary Structure": "public/js/salary_structure.js",
    "Purchase Invoice": "public/js/purchase_invoice.js",
    "Payment Entry": "public/js/payment_entry.js",
    "Payroll Entry": "public/js/payroll_entry.js",
    "Operation": "public/js/operation.js",
    "Quality Procedure": "public/js/doctype/quality_procedure/form.js",
    "ToDo": "public/js/todo.js",
    "Asset Maintenance": "public/js/asset_maintenance.js",
}

doctype_list_js = {
    "Quality Procedure": "public/js/doctype/quality_procedure/list.js",
}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
app_include_icons = "powerpro/icons/igcaribe/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "powerpro.utils.jinja_methods",
# 	"filters": "powerpro.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "powerpro.install.before_install"
# after_install = "powerpro.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "powerpro.uninstall.before_uninstall"
# after_uninstall = "powerpro.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "powerpro.utils.before_app_install"
# after_app_install = "powerpro.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "powerpro.utils.before_app_uninstall"
# after_app_uninstall = "powerpro.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "powerpro.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
    "Customer": "powerpro.utils.query.customer_query_conditions",
    "Quotation": "powerpro.utils.query.quotation_query_conditions",
    "Sales Order": "powerpro.utils.query.sales_order_query_conditions",
    "Sales Invoice": "powerpro.utils.query.sales_invoice_query_conditions",
    "Payment Entry": "powerpro.utils.query.payment_entry_query_conditions",
    "Delivery Note": "powerpro.utils.query.delivery_note_query_conditions",
    "Asset Maintenance Log": "powerpro.utils.query.asset_maintenance_log_query_conditions",
    "ToDo": "powerpro.utils.query.todo_query_conditions",
}
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
    "Quality Procedure": "powerpro.controllers.quality_procedure.QualityProcedure",
    "Custom Field": "powerpro.controllers.custom_field.CustomField",
    "Salary Slip": "powerpro.controllers.salary_slip.SalarySlip",
    "Payroll Entry": "powerpro.controllers.payroll_entry.PayrollEntry",
    "Asset Maintenance": "powerpro.controllers.asset_maintenance.AssetMaintenance",
    "Asset Maintenance Log": "powerpro.controllers.asset_maintenance_log.AssetMaintenanceLog",
    "Web Form": "powerpro.controllers.web_form.WebForm",
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Customer": {
        "on_update": "powerpro.controllers.customer.on_update",
    },
    "Item": {
        "autoname": "powerpro.controllers.item.autoname",
        "before_save": "powerpro.controllers.item.before_save",
    },
    "Sales Invoice": {
        "before_insert": "powerpro.controllers.sales_invoice.before_insert",
        "on_submit": "powerpro.controllers.sales_invoice.on_submit",
        "on_cancel": "powerpro.controllers.sales_invoice.on_cancel",
    },
    "Salary Structure Assignment": {
        "validate": "powerpro.controllers.salary_structure_assignment.validate",
    },
    "Salary Slip": {
        "validate": [
            "powerpro.controllers.salary_slip.helper.set_dgii_payroll_settings",
            "powerpro.controllers.salary_slip.helper.set_mid_month_start",
        ],
    },
    "Timesheet": {
        "before_save": "powerpro.controllers.timesheet.before_save",
        "validate": "powerpro.controllers.timesheet.validate",
    },
    "Purchase Invoice": {
        "validate": "powerpro.controllers.purchase_invoice.validate",
        "before_submit": "powerpro.controllers.purchase_invoice.before_submit",
    },
    "Asset Maintenance Log": {
        "on_update_after_submit": "powerpro.controllers.asset_maintenance_log.on_update_after_submit",
    },
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"powerpro.tasks.all"
# 	],
# 	"daily": [
# 		"powerpro.tasks.daily"
# 	],
# 	"hourly": [
# 		"powerpro.tasks.hourly"
# 	],
# 	"weekly": [
# 		"powerpro.tasks.weekly"
# 	],
# 	"monthly": [
# 		"powerpro.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "powerpro.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
    "hrms.payroll.doctype.salary_slip.salary_lip.make_salary_slip_from_timesheet": "powerpro.controllers.salary_slip.make_salary_slip_from_timesheet",
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "powerpro.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["powerpro.utils.before_request"]
# after_request = ["powerpro.utils.after_request"]

# Job Events
# ----------
# before_job = ["powerpro.utils.before_job"]
# after_job = ["powerpro.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"powerpro.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Boot Info into Session
# ----------------------
boot_session = "powerpro.boot.boot_session"
