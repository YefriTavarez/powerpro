# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


def on_update(doc, *args):
	create_user_permissions_to_portal_users(doc)


def create_user_permissions_to_portal_users(doc):
	# Create user permissions for all portal users

	# if not portal users, then exit the function
	if not doc.portal_users:
		return # exit the function

	# loop through all portal users
	for portal_user in doc.portal_users:
		# check if the user already has a user permission
		permission = frappe.db.exists("User Permission", {
			"user": portal_user.user,
			"allow": "Customer",
			"for_value": doc.name,
		})

		# if the user already has a user permission, then exit the loop
		if permission:
			continue

		# create a new user permission
		permission = frappe.new_doc("User Permission")
		permission.update({
			"user": portal_user.user,
			"allow": "Customer",
			"for_value": doc.name,
			"apply_to_all_doctypes": 1,
			"is_default": 1,
		})

		# save the user permission
		permission.save()
