"""
***************************************************************************************
** WARNING: CRITICAL SECURITY IMPLICATIONS                                          **
***************************************************************************************
This file contains custom logic that modifies a core Frappe function. The changes 
here bypass standard permission validations to enable specific functionality for a 
Assets Maintenance Doctypes. While this modification is necessary for the intended use case, it 
introduces significant security risks if the methods defined here are called outside 
the designated Doctype.


**Recommendations:**
- If possible, isolate this functionality further to mitigate potential risks.
"""


import frappe
import frappe.share
import frappe.utils
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import (
	enqueue_create_notification,
	get_title,
	get_title_html,
)
from frappe.desk.form.document_follow import follow_document
from frappe.utils import escape_html


def get(args=None):
	"""get assigned to"""
	if not args:
		args = frappe.local.form_dict

	return frappe.get_all(
		"ToDo",
		fields=["allocated_to as owner", "name"],
		filters={
			"reference_type": args.get("doctype"),
			"reference_name": args.get("name"),
			"status": ("not in", ("Cancelled", "Closed")),
		},
		limit=5,
	)

@frappe.whitelist()
def add(args=None, *, ignore_permissions=False):
	"""add in someone's to do list
	args = {
	        "assign_to": [],
	        "doctype": ,
	        "name": ,
	        "description": ,
	        "assignment_rule":
	}

	"""
	if not args:
		args = frappe.local.form_dict

	users_with_duplicate_todo = []
	shared_with_users = []

	description = escape_html(
		args.get("description", _("Assignment for {0} {1}").format(args["doctype"], args["name"]))
	)

	for assign_to in frappe.parse_json(args.get("assign_to")):
		filters = {
			"reference_type": args["doctype"],
			"reference_name": args["name"],
			"status": "Open",
			"allocated_to": assign_to,
		}
		if not ignore_permissions:
			frappe.get_doc(args["doctype"], args["name"]).check_permission()

		if frappe.get_all("ToDo", filters=filters):
			users_with_duplicate_todo.append(assign_to)
		else:
			from frappe.utils import nowdate

            # the only changes here is adding item_code and item_name to args
			d = frappe.get_doc(
				{
					"doctype": "ToDo",
					"allocated_to": assign_to,
					"reference_type": args["doctype"],
					"reference_name": args["name"],
					"description": f"{args.get('description')} - {args.get('item_name')}",
					"priority": args.get("priority", "Medium"),
					"status": "Open",
					"date": args.get("date", nowdate()),
					"assigned_by": "Administrator", # Super user is the default assigned_by to bypass permision query
					"assignment_rule": args.get("assignment_rule"),
					"item_code": args.get("item_code"),
					"item_name": args.get("item_name"),
					"asset_name": args.get("asset_name"),
					"maintenance_team": args.get("maintenance_team"),
					"periodicity": args.get("periodicity"),
					"asset_maintenance_log": args.get("asset_maintenance_log"),
					"assigne_name": args.get("assigne_name"),
				}
			).insert(ignore_permissions=True)

			# set assigned_to if field exists
			if frappe.get_meta(args["doctype"]).get_field("assigned_to"):
				frappe.db.set_value(args["doctype"], args["name"], "assigned_to", assign_to)

			doc = frappe.get_doc(args["doctype"], args["name"])

			# If assignee does not have permissions, share or inform
			# Commented out because it is not needed, we just need to update the maintenance log
			# if not frappe.has_permission(doc=doc, user=assign_to):
			# 	if frappe.get_system_settings("disable_document_sharing"):
			# 		msg = _("User {0} is not permitted to access this document.").format(
			# 			frappe.bold(assign_to)
			# 		)
			# 		msg += "<br>" + _(
			# 			"As document sharing is disabled, please give them the required permissions before assigning."
			# 		)
			# 		frappe.throw(msg, title=_("Missing Permission"))
			# 	else:
			# 		frappe.share.add(doc.doctype, doc.name, assign_to)
			# 		shared_with_users.append(assign_to)

			# make this document followed by assigned user
			if frappe.get_cached_value("User", assign_to, "follow_assigned_documents"):
				follow_document(args["doctype"], args["name"], assign_to)

			# notify
			notify_assignment(
				d.assigned_by,
				d.allocated_to,
				d.reference_type,
				d.reference_name,
				action="ASSIGN",
				description=description,
			)

	if shared_with_users:
		user_list = format_message_for_assign_to(shared_with_users)
		frappe.msgprint(
			_("Shared with the following Users with Read access:{0}").format(user_list, alert=True)
		)

	if users_with_duplicate_todo:
		user_list = format_message_for_assign_to(users_with_duplicate_todo)
		frappe.msgprint(_("Already in the following Users ToDo list:{0}").format(user_list, alert=True))

	return get(args)


def notify_assignment(assigned_by, allocated_to, doc_type, doc_name, action="CLOSE", description=None):
	"""
	Notify assignee that there is a change in assignment
	"""
	if not (assigned_by and allocated_to and doc_type and doc_name):
		return

	assigned_user = frappe.db.get_value("User", allocated_to, ["language", "enabled"], as_dict=True)

	# return if self assigned or user disabled
	if assigned_by == allocated_to or not assigned_user.enabled:
		return

	# Search for email address in description -- i.e. assignee
	user_name = frappe.get_cached_value("User", frappe.session.user, "full_name")
	title = get_title(doc_type, doc_name)
	description_html = f"<div>{description}</div>" if description else None

	if action == "CLOSE":
		subject = _("Your assignment on {0} {1} has been removed by {2}", lang=assigned_user.language).format(
			frappe.bold(_(doc_type)), get_title_html(title), frappe.bold(user_name)
		)
	else:
		user_name = frappe.bold(user_name)
		document_type = frappe.bold(_(doc_type, lang=assigned_user.language))
		title = get_title_html(title)
		subject = _("{0} assigned a new task {1} {2} to you", lang=assigned_user.language).format(
			user_name, document_type, title
		)

	notification_doc = {
		"type": "Assignment",
		"document_type": doc_type,
		"subject": subject,
		"document_name": doc_name,
		"from_user": frappe.session.user,
		"email_content": description_html,
	}

	enqueue_create_notification(allocated_to, notification_doc)


def format_message_for_assign_to(users):
	return "<br><br>" + "<br>".join(users)