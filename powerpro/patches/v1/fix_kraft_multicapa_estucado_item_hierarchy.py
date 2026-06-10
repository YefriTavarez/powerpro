import frappe


ITEM_CODES = (
	"1114-003",
	"1113-006",
	"1113-005",
	"1119-110",
	"1113-003",
	"1114-002",
	"1119-106",
	"1119-105",
	"1119-104",
	"1119-103",
	"1119-102",
	"1119-099",
	"1119-098",
	"1119-097",
	"1119-096",
	"1119-095",
	"1119-094",
	"1119-088",
	"1119-087",
	"1119-086",
	"1119-085",
	"1119-084",
	"1119-082",
	"1119-079",
	"1119-071",
	"1119-069",
	"1119-068",
	"1119-066",
	"1119-065",
	"1119-061",
	"1119-060",
	"1119-059",
	"1119-058",
	"1119-057",
	"1119-056",
	"1119-055",
	"1119-051",
	"1119-048",
	"1119-047",
	"1119-045",
	"1119-041",
	"1119-036",
	"1119-035",
	"1119-031",
	"1119-030",
	"1119-027",
	"1119-026",
	"1119-021",
	"1119-020",
	"1119-019",
	"1119-018",
	"1119-013",
	"1119-008",
	"1119-007",
	"1119-006",
	"1119-003",
	"1119-001",
)


TARGET_VALUES = {
	"item_group": "Kraft Multicapa Estucado",
	"custom_item_group_1": "Artículos",
	"custom_item_group_2": "Materia Prima",
	"custom_item_group_3": "Cartón",
	"custom_item_group_4": "Kraft Multicapa Estucado",
	"custom_item_group_5": None,
}


def execute():
	target_group_number = frappe.db.get_value(
		"Item Group",
		TARGET_VALUES["item_group"],
		"item_group_number",
	)

	if not target_group_number:
		frappe.throw(
			f"El grupo de artículos '{TARGET_VALUES['item_group']}' no tiene un número asignado."
		)

	placeholders = ", ".join(["%s"] * len(ITEM_CODES))
	items = frappe.db.sql_list(
		f"""
		select name
		from `tabItem`
		where name in ({placeholders})
			or item_code in ({placeholders})
		order by name
		""",
		(*ITEM_CODES, *ITEM_CODES),
	)

	for item in items:
		frappe.db.set_value("Item", item, TARGET_VALUES, update_modified=False)

		if item.startswith(f"{target_group_number}-"):
			frappe.db.set_value("Item", item, "item_code", item, update_modified=False)
			continue

		new_item_code = get_next_item_code(target_group_number, item)
		frappe.rename_doc(
			"Item",
			item,
			new_item_code,
			force=True,
			show_alert=False,
			rebuild_search=False,
		)
		frappe.db.set_value("Item", new_item_code, TARGET_VALUES, update_modified=False)
		frappe.db.set_value("Item", new_item_code, "item_code", new_item_code, update_modified=False)


def get_next_item_code(group_number, current_item):
	existing = frappe.db.sql_list(
		"""
		select name
		from `tabItem`
		where name like %s
			and name != %s
		union
		select item_code
		from `tabItem`
		where item_code like %s
			and name != %s
		""",
		(
			f"{group_number}-%",
			current_item,
			f"{group_number}-%",
			current_item,
		),
	)

	used = [
		int(code.split("-")[1])
		for code in existing
		if code and "-" in code and code.split("-")[1].isdigit()
	]

	return f"{group_number}-{max(used or [0]) + 1:03d}"
