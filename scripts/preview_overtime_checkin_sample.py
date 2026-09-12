"""Read a bounded DEV checkin sample; never approve evidence or write documents.

Run with the bench virtualenv from sites/, passing an employee and up to seven
ISO work dates. JSON goes to stdout. This is a CLI diagnostic, not an RPC endpoint.
The current flags remain authoritative. Counterfactuals explicitly assume that
the exclusions, synchronization and proposed extension have been reviewed.
"""
import argparse
from copy import deepcopy
from datetime import date, timedelta
import hashlib
import json
from unittest.mock import patch

import frappe
from frappe.utils import get_datetime, getdate, now_datetime

SITE = "igcaribe.fortabs.com"
COUNTS = ("Employee Checkin", "Attendance", "Overtime Authorization",
          "Retroactive Overtime Adjustment", "Overtime Pay Policy",
          "Overtime Reconciliation Run", "Additional Salary", "Salary Slip",
          "Leave Allocation", "Leave Application", "Overtime Compensatory Credit",
          "Overtime Settlement Election", "Version", "Error Log", "Notification Log")
PUNCH_FIELDS = ["name", "time", "log_type", "shift", "shift_start", "shift_end",
                "shift_actual_start", "shift_actual_end", "skip_auto_attendance",
                "offshift", "modified"]
SHIFT_FIELDS = ["name", "modified", "start_time", "end_time", "enable_auto_attendance",
                "last_sync_of_checkin", "determine_check_in_and_check_out",
                "working_hours_calculation_based_on", "begin_check_in_before_shift_start_time",
                "allow_check_out_after_shift_end_time"]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def sample(employee, dates):
    from powerpro.controllers.overtime import get_schedule_context
    from powerpro.payroll_rules.overtime_evidence import evaluate_evidence
    from powerpro.payroll_rules.overtime_pay_policy import classify_night_session
    from powerpro.payroll_rules.overtime_shift_evidence import ALTERNATING, STRICT, FIRST_LAST, EVERY_PAIR

    if frappe.local.site != SITE or not frappe.conf.developer_mode or frappe.session.user != "Administrator":
        raise frappe.PermissionError("Requires Administrator on the explicit Development site")
    if not 1 <= len(dates) <= 7 or len(set(dates)) != len(dates):
        raise ValueError("Select one to seven distinct work dates")
    days = sorted(date.fromisoformat(day) for day in dates)
    now = now_datetime()
    if any(day >= now.date() for day in days):
        raise ValueError("Only completed historical dates may be sampled")
    emp = frappe.db.get_value("Employee", employee, ["name", "company", "default_shift", "holiday_list"], as_dict=True)
    if not emp:
        raise ValueError("Employee not found")

    def inputs(day):
        assignments = frappe.get_all("Shift Assignment", filters={"employee": employee,
            "docstatus": 1, "status": "Active", "start_date": ["<=", day]},
            fields=["name", "shift_type", "start_date", "end_date", "modified"], limit_page_length=1001)
        if len(assignments) > 1000:
            raise ValueError("Too many assignments")
        assignments = [r for r in assignments if not r.end_date or getdate(r.end_date) >= day]
        shifts = {r.shift_type for r in assignments} or {emp.default_shift}
        if len(shifts) != 1 or not next(iter(shifts)):
            raise ValueError("The day needs an unambiguous assigned or default shift")
        name = next(iter(shifts))
        shift = frappe.db.get_value("Shift Type", name, SHIFT_FIELDS, as_dict=True)
        holiday_list = emp.holiday_list or frappe.db.get_value("Shift Type", name, "holiday_list") or frappe.db.get_value("Company", emp.company, "default_holiday_list")
        context = dict(get_schedule_context(day, name, holiday_list), date=str(day))
        if get_datetime(context["shift_end"]).date() != day:
            raise ValueError("This sample tool covers daytime shifts; use the overnight review for cross-date shifts")
        rows = frappe.get_all("Employee Checkin", filters=[["employee", "=", employee],
            ["time", ">=", day], ["time", "<", day + timedelta(days=1)]],
            fields=PUNCH_FIELDS, order_by="time asc, name asc", limit_page_length=201)
        if not rows or len(rows) > 200:
            raise ValueError("The sample needs 1 to 200 punches per day")
        sources = []
        for dt in ["Overtime Authorization", "Retroactive Overtime Adjustment"]:
            sources.extend(dict(r, doctype=dt) for r in frappe.get_all(dt,
                filters={"employee": employee, "work_date": day},
                fields=["name", "docstatus", "authorization_start", "authorization_end", "modified"], limit_page_length=101))
        if len(sources) > 100:
            raise ValueError("Too many existing sources for a diagnostic sample")
        return dict(shift=shift, context=context, rows=rows, assignments=assignments, sources=sources)

    settings_fields = ["enable_checkin_overtime_reconciliation", "checkin_overtime_effective_from",
                       "start_night_hours", "end_night_hours", "extra_hours_rate",
                       "extraordinary_hours_rate", "night_hours_rate", "max_weekly_extra_hours"]

    def configuration():
        return {"scheduler": frappe.db.get_single_value("System Settings", "enable_scheduler"),
                "payroll": {key: frappe.db.get_single_value("DGII Payroll Settings", key) for key in settings_fields}}

    before = {dt: frappe.db.count(dt) for dt in COUNTS}
    config = configuration()
    cases = []
    for day in days:
        data = inputs(day)
        original_hash = digest(data)
        shift, context, rows = data["shift"], data["context"], data["rows"]
        start = get_datetime(context["shift_end"])
        end = max(start + timedelta(minutes=1), get_datetime(rows[-1].time))
        if end.date() != day:
            raise ValueError("Proposed extension crosses the supported sample boundary")
        authorization = dict(name="UNSAVED-SAMPLE-" + str(day), shift=shift.name,
            start=start.isoformat(), end=end.isoformat(), maximum_hours=(end-start).total_seconds()/3600)
        competing = any(r["docstatus"] == 1 and get_datetime(r["authorization_start"]) < end
            and get_datetime(r["authorization_end"]) > start for r in data["sources"])

        def evaluate(proposed_rows, proposed_shift):
            return evaluate_evidence(authorization=authorization, rows=proposed_rows, shift=proposed_shift,
                contexts=[context], next_windows=[], now=now, competing=competing)

        current = evaluate(rows, shift)
        variants = []
        for direction in [ALTERNATING, STRICT]:
            for calculation in [FIRST_LAST, EVERY_PAIR]:
                hypothetical_rows = deepcopy(rows)
                for row in hypothetical_rows:
                    row.skip_auto_attendance = 0
                hypothetical_shift = dict(shift, determine_check_in_and_check_out=direction,
                    working_hours_calculation_based_on=calculation,
                    last_sync_of_checkin=end + timedelta(minutes=float(shift.allow_check_out_after_shift_end_time or 0)))
                result = evaluate(hypothetical_rows, hypothetical_shift)
                night = []
                if result.get("worked_intervals"):
                    for basis in ["Clock overlap", "Whole nocturnal session"]:
                        night.append(classify_night_session(result["worked_intervals"],
                            result["calculation"]["intervals"], basis=basis))
                variants.append(dict(direction=direction, hours_rule=calculation,
                    evidence_state=result["state"], issues=result["issues"],
                    sessions=result.get("sessions", []), worked_intervals=result.get("worked_intervals", []),
                    interpretations=result.get("interpretations", []), night=night,
                    proposed_authorized_hours=result.get("calculation", {}).get("verified_hours"),
                    unapproved_intervals=result.get("calculation", {}).get("unapproved_intervals", []),
                    settlement_ready=False, weekly_bands_validated=False))
        assert digest(data) == original_hash, "Simulation changed original input in memory"
        assert digest(inputs(day)) == original_hash, "Source data changed during the preview"
        cases.append(dict(date=str(day), source_hash=original_hash, source=data,
            proposed_unsaved_window=authorization, diagnostic_with_current_flags=current,
            hypothetical_variants=variants))
    after = {dt: frappe.db.count(dt) for dt in COUNTS}
    assert before == after and config == configuration(), "Site state changed during preview"
    return dict(site=SITE, employee=emp, generated_at=now, read_only=True,
        saved_documents=0, approved=False, settlement_ready=False, configuration=config,
        counts=after, source_hashes_rechecked=True, database_counts_unchanged=True, cases=cases,
        assumptions=[
            "Every extension is proposed in memory from scheduled shift end to the final same-day punch; it is not an authorization.",
            "When the last punch precedes shift end, a one-minute probe window is used only to inspect incomplete evidence.",
            "Current flags and existing source states are preserved. Hypothetical variants alone assume exclusions reviewed and synchronization complete.",
            "Raw timestamps and IN/OUT directions are never changed, even in the hypothetical variants.",
            "Current shift/calendar settings are not proof of historical settings. Weekly evidence, approval and payroll rates are not validated here.",
            "A hypothetical Verified result is not accepted attendance, payable hours, or permission to settle.",
            "No overnight, holiday or full-nocturnal-session pilot coverage is implied by this daytime sample."])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("employee")
    parser.add_argument("dates", nargs="+")
    args = parser.parse_args()
    frappe.init(site=SITE)
    frappe.connect()
    sql = frappe.db.sql

    def only_select(query, *args, **kwargs):
        if not str(query).lstrip().lower().startswith(("select", "show", "describe", "explain")):
            raise AssertionError("Diagnostic attempted non-read SQL")
        return sql(query, *args, **kwargs)

    def forbidden(*args, **kwargs):
        raise AssertionError("Diagnostic attempted a commit or outbound action")

    try:
        with (patch.object(frappe.db, "sql", only_select), patch.object(frappe.db, "commit", forbidden),
              patch.object(frappe, "enqueue", forbidden), patch.object(frappe, "sendmail", forbidden),
              patch.object(frappe, "log_error", forbidden)):
            result = sample(args.employee, args.dates)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str, indent=2))
    finally:
        frappe.db.rollback()
        frappe.destroy()


if __name__ == "__main__":
    main()
