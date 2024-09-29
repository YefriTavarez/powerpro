# Copyright (c) 2024, Miguel Higuera and Contributors
# For license information, please see license.txt

import frappe
from frappe.utils import (
    get_date_str,
    time_diff_in_hours,
    flt,
    get_timedelta,
    get_time_str,
    get_datetime_str,
)


def get_dgii_payroll_settings():
    doctype = "DGII Payroll Settings"
    return frappe.get_single(doctype)


payroll_settings = get_dgii_payroll_settings()


def before_save(doc, method):
    set_default_night_hours(doc, payroll_settings)


def validate(doc, method):
    # set_total_expected_hours(doc)
    set_total_missing_hours(doc)
    set_total_expected_hours(doc, payroll_settings)
    set_total_extra_hours(doc, payroll_settings)
    set_extraordinary_hours(doc, payroll_settings)
    set_night_hours(doc)


def set_default_night_hours(doc, payroll_settings):
    for row in doc.time_logs:
        row.start_night_hours = payroll_settings.start_night_hours
        row.end_night_hours = payroll_settings.end_night_hours


def set_total_missing_hours(doc):
    total_missing_hours = 0

    if doc.total_hours < doc.total_expected_hours:
        total_missing_hours = doc.total_expected_hours - doc.total_hours

    doc.total_missing_hours = total_missing_hours


def set_total_expected_hours(doc, payroll_settings):
    weekly_expected_hours = payroll_settings.weekly_expected_hours
    doc.total_expected_hours = weekly_expected_hours

    # for row in doc.time_logs:
    #     total_expected_hours += row.expected_hours

    # if total_expected_hours > weekly_expected_hours:
    #     total_expected_hours = 44

    # doc.total_expected_hours = total_expected_hours


def set_total_extra_hours(doc, payroll_settings):
    total_extra_hours = 0
    max_extra_hours = payroll_settings.max_weekly_extra_hours
    expected_hours = payroll_settings.weekly_expected_hours

    # we need to sum the hours between the expected hours and the max extra hours
    # Example:
    # If one employee has 74 hours, the total extra hours must be the qty 
    # of hours between 44 and 68, in this case, 24 hours
    if doc.total_hours > expected_hours:
        total_extra_hours = doc.total_hours - expected_hours

    if doc.total_hours > max_extra_hours:
        total_extra_hours = max_extra_hours - expected_hours

    doc.extra_hours = total_extra_hours


def set_extraordinary_hours(doc, payroll_settings):
    extraordinary_hours = 0
    weekly_extraordinary_hours = payroll_settings.max_weekly_extra_hours

    if doc.total_hours > weekly_extraordinary_hours:
        extraordinary_hours = doc.total_hours - weekly_extraordinary_hours
        doc.extraordinary_hours = extraordinary_hours
    else:
        doc.extraordinary_hours = 0


def set_night_hours(doc):
    night_hours = 0

    for row in doc.time_logs:
        to_time = get_time_str(get_timedelta(get_datetime_str(row.to_time)))
        start_night_hours = get_time_str(row.start_night_hours)
        end_night_hours = get_time_str(row.end_night_hours)

        diff_start_hours = time_diff_in_hours(to_time, start_night_hours)
        diff_end_hours = time_diff_in_hours(to_time, end_night_hours)

        """
        to_time is datetime field, and exists the following cases:

        1. if to time is greather than start_night_hours, 
            then the night hours is the difference between to_time and start_night_hours
            otherwise, the night hours is 0
        
        2. if to time is between start_night_hours and end_night_hour,
            like to_time = 03:00:00, start_night_hours = 21:00:00, end_night_hour = 06:00:00

            in this example, the night hours should be 6 hours because 
                a. there is 3 hours between start_night_hours and "23:59:59"
                b. there is 3 hours between "00:00:00" and to_time

        
        3. if to time is less than start_night_hours,
            then the night hours is 0
        """

        if diff_start_hours > 0 and to_time < "23:59:59":
            night_hours += diff_start_hours

        if to_time > "00:00:00" and to_time < end_night_hours and diff_start_hours < 0 and diff_end_hours < 0:
            diff_start_hours = time_diff_in_hours("23:59:59", start_night_hours)
            diff_end_hours = time_diff_in_hours(to_time, "00:00:00")

            night_hours += diff_start_hours + diff_end_hours

    doc.night_hours = round(night_hours, 2)
