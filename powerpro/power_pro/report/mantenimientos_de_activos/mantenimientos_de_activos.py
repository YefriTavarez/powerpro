# Copyright (c) 2024, Miguel Higuera and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    return get_columns(filters), get_data(filters)


def get_columns(filters):
    if filters.get("summary"):
        return get_summary_columns()

    columns = [
        _("Asset Maintenance") + ":Link/Asset Maintenance:120",
        _("Asset") + ":Link/Asset:100",
        _("Maintenance Team") + ":Link/Asset Maintenance Team:150",
        _("Item Code") + ":Link/Item:100",
        _("Item Name") + ":Data:150",
        _("Maintenance Manager Name") + ":Data:150",
        _("Assigned To") + ":Data:150",
        _("Task Name") + ":Data:150",
        _("Maintenance Status") + ":Data:150",
        _("Periodicity") + ":Data:150",
        _("Due Date") + ":Date:150",
        _("Completion Date") + ":Date:150",
        _("Completed By") + ":Data:150",
        _("Maintenance Type") + ":Data:150",
        _("Asset Maintenance Log") + ":Link/Asset Maintenance Log:100",
    ]

    return columns


def get_summary_columns():
    columns = [
        _("Maquinaria") + ":Data:250",
        _("Periodicity") + ":Data:100",
        _("Task") + ":Data:300",
        _("Planned") + ":Data:150",
        _("Completed") + ":Data:150",
        _("Overdue") + ":Data:150",
        _("Cancelled") + ":Data:150",
        _("Asset Maintenance") + ":Link/Asset Maintenance:120",
        _("Asset") + ":Link/Asset:100",
        _("Maintenance Manager Name") + ":Data:150",
    ]

    return columns


def get_data(filters):
    if filters.get("summary"):
        return get_summary_data(filters)

    return get_detailed_data(filters)


def get_summary_data(filters):
    # We need to sum every task status and show only one row per asset maintenance
    query = frappe.db.sql("""
        Select
            asset_maintenance.item_name,
            asset_maintenance_log.periodicity,
            asset_maintenance_log.task_name,
            Count(Case When asset_maintenance_log.maintenance_status = 'Planned' Then 1 End),
            Count(Case When asset_maintenance_log.maintenance_status = 'Completed' Then 1 End),
            Count(Case When asset_maintenance_log.maintenance_status = 'Overdue' Then 1 End),
            Count(Case When asset_maintenance_log.maintenance_status = 'Cancelled' Then 1 End),
            asset_maintenance.name,
            asset_maintenance.asset_name,
            asset_maintenance.maintenance_manager_name
        From
            `tabAsset Maintenance` as asset_maintenance
        Inner Join
            `tabAsset Maintenance Log` as asset_maintenance_log
        On
            asset_maintenance.name = asset_maintenance_log.asset_maintenance
        Where
            {filters}
        Group By
            asset_maintenance.name,
            asset_maintenance.asset_name,
            asset_maintenance.item_name,
            asset_maintenance_log.periodicity,
            asset_maintenance_log.task_name
    """.format(filters=get_filters(filters)), as_list=1)

    for row in query:
        row[1] = _(row[1])

    return query


def get_detailed_data(filters):
    query = frappe.db.sql("""
        Select
            asset_maintenance.name,
            asset_maintenance.asset_name,
            asset_maintenance.maintenance_team,
            asset_maintenance.item_code,
            asset_maintenance.item_name,
            asset_maintenance.maintenance_manager_name,
            asset_maintenance_log.assign_to_name,
            asset_maintenance_log.task_name,
            asset_maintenance_log.maintenance_status,
            asset_maintenance_log.periodicity,
            asset_maintenance_log.due_date,
            asset_maintenance_log.completion_date,
            asset_maintenance_log.completed_by_name,
            asset_maintenance_log.maintenance_type,
            asset_maintenance_log.name
        From
            `tabAsset Maintenance` as asset_maintenance
        Inner Join
            `tabAsset Maintenance Log` as asset_maintenance_log
        On
            asset_maintenance.name = asset_maintenance_log.asset_maintenance
        Where
            {filters}
        Order By
            asset_maintenance.name,
            asset_maintenance_log.due_date
    """.format(filters=get_filters(filters)), as_list=1)

    previous_asset_maintenance = None

    for row in query:
        asset_maintenance = row[0]

        # translate rows
        row[8] = _(row[8])
        row[9] = _(row[9])
        row[13] = _(row[13])

        if asset_maintenance == previous_asset_maintenance:
            for idx in range(0, 6):
                row[idx] = None

            row[13] = None

        previous_asset_maintenance = asset_maintenance

    return query


def get_filters(filters):
    conditions = ['asset_maintenance_log.docstatus = 1']

    if filters.get("from_date") and filters.get("to_date"):
        conditions.append(
            f"asset_maintenance_log.due_date between {filters.get('from_date')!r} and {filters.get('to_date')!r}"
        )

    if filters.get("asset_maintenance"):
        conditions.append(
            f"asset_maintenance_log.asset_maintenance = {filters.get('asset_maintenance')!r}"
        )

    if filters.get("asset"):
        conditions.append(
            f"asset_maintenance.asset_name = {filters.get('asset')!r}"
        )

    if filters.get("maintenance_team"):
        conditions.append(
            f"asset_maintenance.maintenance_team = {filters.get('maintenance_team')!r}"
        )

    if filters.get("maintenance_status"):
        conditions.append(
            f"asset_maintenance_log.maintenance_status = {filters.get('maintenance_status')!r}"
        )

    if filters.get("periodicity"):
        conditions.append(
            f"asset_maintenance_log.periodicity = {filters.get('periodicity')!r}"
        )

    return " And ".join(conditions)    
