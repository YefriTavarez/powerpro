"""Site-free tests of the real manual service using an in-memory Frappe adapter.

No bench, site, payroll, leave or database is touched. Real MariaDB concurrency,
permissions and Dieta hooks must additionally be checked in isolated staging.
"""
import copy
from datetime import datetime, date
import html
import importlib
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Avoid PowerPro's legacy package-level Frappe monkey patch in site-free tests.
pkg = types.ModuleType("powerpro"); pkg.__path__ = [str(ROOT / "powerpro")]
sys.modules["powerpro"] = pkg

class Record(dict):
    def __getattr__(self, name): return self.get(name)
    def __setattr__(self, name, value): self[name] = value
    def check_permission(self, action):
        if action in self.get("denied", []): raise PermissionError(action)
    def reload(self): self.update(copy.deepcopy(STORE[(self.doctype, self.name)])); return self
    def db_set(self, values, *args, **kwargs):
        if isinstance(values, str): values = {values: args[0]}
        self.update(values); self.modified = str(len(WRITES) + 1)
        STORE[(self.doctype, self.name)] = copy.deepcopy(self)
        WRITES.append((self.doctype, self.name, copy.deepcopy(values)))
    def add_comment(self, kind, text): COMMENTS.append((self.name, kind, text))
    def get_doc_before_save(self): return self.get("before")

NOW = datetime(2026, 9, 14, 12)
STORE, WRITES, COMMENTS, LOCKS = {}, [], [], []
SETTINGS = Record()
ROLES = []

def get_doc(dt, name=None, **kwargs):
    if kwargs.get("for_update"): LOCKS.append((dt, name))
    if dt == "DGII Payroll Settings": return SETTINGS
    return Record(copy.deepcopy(STORE[(dt, name)]))

def matches(doc, filters):
    for field, value in filters.items():
        actual = doc.get(field)
        if isinstance(value, list):
            op, expected = value
            if op == 'not in' and actual in expected: return False
            if op == '>' and not actual > expected: return False
            if op == '<' and not actual < expected: return False
            if op == 'between' and not str(expected[0]) <= str(actual) <= str(expected[1]): return False
        elif actual != value: return False
    return True

def get_all(dt, filters=None, fields=None, pluck=None, **kwargs):
    docs = [d for (t,n),d in STORE.items() if t == dt and matches(d, filters or {})]
    if pluck: return [d[pluck] for d in docs]
    result = []
    for doc in docs:
        row = Record()
        for field in fields or list(doc):
            parts = field.split(' as '); row[parts[-1]] = doc.get(parts[0])
        result.append(row)
    return result

class DB:
    def get_values(self, dt, fieldname=None, **kwargs):
        if kwargs.get("for_update"): LOCKS.append((dt, "rows"))
        return get_all(dt, fields=fieldname, **kwargs)
    def set_value(self, *args, **kwargs):
        raise AssertionError("Unexpected database write in site-free regression")
    def get_value(self, dt, name, field, **kwargs):
        if kwargs.get("for_update"): LOCKS.append((dt, name))
        if dt == "Role": return 0 if field == "disabled" else int(name in ["HR Manager", "System Manager", "Custom Approver"])
        return STORE.get((dt, name), {}).get(field)
    def exists(self, dt, name): return dt == "DocType"

def throw(message, exc=ValueError, **kwargs): raise exc(message)
frappe = types.ModuleType("frappe"); frappe.__path__ = []
frappe._ = lambda text: text
frappe._dict = Record
frappe.throw = throw
frappe.bold = lambda value: str(value)
frappe.PermissionError = PermissionError
frappe.ValidationError = ValueError
frappe.whitelist = lambda *args, **kwargs: lambda function: function
frappe.session = Record(user="manager@example.test")
frappe.get_doc = get_doc
frappe.get_all = get_all
frappe.get_single = lambda name: SETTINGS
frappe.get_roles = lambda user: ROLES
frappe.has_permission = lambda dt, action, doc=None: action not in (doc or {}).get("denied", [])
frappe.db = DB()
sys.modules["frappe"] = frappe
utils = types.ModuleType("frappe.utils")
utils.cint = lambda value: int(value or 0)
utils.flt = lambda value: float(value or 0)
utils.get_datetime = lambda value: value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
utils.getdate = lambda value: value if isinstance(value, date) and not isinstance(value, datetime) else datetime.fromisoformat(str(value)).date()
utils.now_datetime = lambda: NOW
utils.escape_html = html.escape
utils.get_link_to_form = lambda *args: "link"
sys.modules["frappe.utils"] = utils
model = types.ModuleType("frappe.model"); model.__path__ = []
sys.modules["frappe.model"] = model
mod = types.ModuleType("frappe.model.document"); mod.Document = Record
sys.modules["frappe.model.document"] = mod

from powerpro.controllers import manual_overtime as service, overtime
from powerpro.payroll_rules.manual_overtime import normalize_intervals
from powerpro.power_pro.doctype.overtime_work_call import overtime_work_call as calls
from powerpro.power_pro.doctype.overtime_authorization.overtime_authorization import OvertimeAuthorization
from powerpro.power_pro.doctype.dgii_payroll_settings.dgii_payroll_settings import DGIIPayrollSettings
from powerpro.controllers import overtime_settlement as settlement


def auth(name="AUTH", **extra):
    doc = Record(doctype="Overtime Authorization", name=name, employee="EMP", employee_name="Employee One",
                 docstatus=1, status="Approved", work_date="2026-09-13", authorization_start="2026-09-13 07:00:00",
                 authorization_end="2026-09-13 12:00:00", maximum_hours=5, modified="0", overtime_work_call="CALL",
                 verified_hours=0, regular_35_hours=0, regular_100_hours=0, reconciliation_status="Scheduled",
                 settlement_status="Pending", planned_settlement="Compensatory Rest", day_classification="Weekly Rest")
    doc.update(extra); STORE[(doc.doctype, name)] = doc
    return doc

class ManualOvertimeTest(unittest.TestCase):
    def setUp(self):
        STORE.clear(); WRITES.clear(); COMMENTS.clear(); LOCKS.clear()
        SETTINGS.clear(); SETTINGS.update(enable_overtime_authorization=1, enable_manual_overtime_verification=1,
            overtime_manual_verification_roles="Custom Approver", weekly_expected_hours=44, max_weekly_extra_hours=68,
            start_night_hours="21:00", end_night_hours="07:00", extra_hours_rate=35, extraordinary_hours_rate=100, night_hours_rate=15)
        ROLES[:] = ["Custom Approver"]
        frappe.session.user = "manager@example.test"
        auth()
        STORE[("Overtime Work Call", "CALL")] = Record(doctype="Overtime Work Call", name="CALL", docstatus=1,
                                                     authorization_count=1, status="Authorized")
        self.context = {"checkins": [], "classification": "Weekly Rest", "shift_start": None, "shift_end": None,
                        "warnings": ["No Employee Checkin evidence was found for this work date."],
                        "holiday_list": "2026", "holiday_descriptions": ["Domingo"]}
        self.patches = [patch.object(overtime, "_get_context", side_effect=lambda doc, **kwargs: copy.deepcopy(self.context)),
                        patch.object(overtime, "_get_verified_regular_overtime_before", return_value=0)]
        for p in self.patches: p.start(); self.addCleanup(p.stop)
        self.args = dict(authorization="AUTH", intervals=[{"start":"2026-09-13 07:00:00", "end":"2026-09-13 12:00:00"}], reason="Supervisor confirmed actual attendance")

    def preview(self): return service.preview_manual_verification(**self.args)
    def approve(self, preview=None):
        preview = preview or self.preview()
        return service.approve_manual_verification(**self.args, preview_token=preview["preview_token"])

    def test_preview_without_checkins_is_read_only_and_eligible(self):
        p = self.preview()
        self.assertEqual(p['snapshot']['verified_hours'], 5)
        self.assertEqual(p['snapshot']['weekly_rest_hours'], 5)
        self.assertEqual(p['snapshot']['reconciliation_status'], 'Completed')
        self.assertEqual(p['checkin_comparison']['source_checkins'], [])
        self.assertEqual(p['hours_difference'], 5)
        self.assertFalse(WRITES); self.assertFalse(COMMENTS)

    def test_approval_saves_audit_and_team_totals_without_settlement(self):
        result = self.approve()
        doc = get_doc('Overtime Authorization','AUTH')
        self.assertEqual(result['settlement_status'], 'Pending')
        self.assertEqual(doc.reconciled_by, 'manager@example.test')
        self.assertEqual(doc.reconciliation_source, 'Manual Verification')
        self.assertEqual(json.loads(doc.source_checkins), [])
        self.assertEqual(get_doc('Overtime Work Call','CALL').verified_hours, 5)
        self.assertEqual(get_doc('Overtime Work Call','CALL').status, 'Completed')
        self.assertEqual({w[0] for w in WRITES}, {'Overtime Authorization','Overtime Work Call'})
        self.assertEqual(len(COMMENTS), 2)
        self.assertIn('before', COMMENTS[0][2]); self.assertIn('after', COMMENTS[0][2])
        self.assertLess(LOCKS.index(('Overtime Work Call','CALL')), LOCKS.index(('Employee','EMP')))
        self.assertLess(LOCKS.index(('Employee','EMP')), LOCKS.index(('Overtime Authorization','AUTH')))
        settlement._validate_ready(doc)

    def test_disabled_feature_blocks_preview_and_direct_approval(self):
        SETTINGS.enable_manual_overtime_verification = 0
        for fn in (self.preview, lambda: service.approve_manual_verification(**self.args, preview_token='x')):
            with self.assertRaises(PermissionError): fn()
        self.assertFalse(WRITES)

    def test_role_is_read_from_settings_not_hardcoded(self):
        SETTINGS.overtime_manual_verification_roles = 'System Manager'
        with self.assertRaises(PermissionError): self.preview()
        ROLES[:] = ['System Manager']; self.preview()
        SETTINGS.overtime_manual_verification_roles = ''
        with self.assertRaises(PermissionError): self.preview()

    def test_administrator_does_not_bypass_configured_roles(self):
        frappe.session.user='Administrator'; ROLES[:] = ['System Manager']
        with self.assertRaises(PermissionError): self.preview()

    def test_removed_role_after_preview_blocks_approval(self):
        p=self.preview(); SETTINGS.overtime_manual_verification_roles='HR Manager'
        with self.assertRaises(PermissionError): self.approve(p)
        self.assertFalse(WRITES)

    def test_authorization_and_work_call_permissions_checked(self):
        for dt,name in [('Overtime Authorization','AUTH'),('Overtime Work Call','CALL')]:
            STORE[(dt,name)].denied=['write']
            with self.assertRaises(PermissionError): self.preview()
            STORE[(dt,name)].denied=[]
        self.assertFalse(WRITES)

    def test_future_authorization_cannot_be_certified(self):
        STORE[('Overtime Authorization','AUTH')].authorization_end='2026-09-15 12:00:00'
        with self.assertRaisesRegex(ValueError,'not ended'): self.preview()

    def test_draft_cancelled_and_settled_sources_rejected(self):
        for changes in [{'docstatus':0},{'status':'Cancelled'},{'settlement_status':'Credited'},
                        {'settlement_status':'Created'},{'settlement_status':'Paid'},{'settlement_status':'Cancelled'}]:
            auth(**changes)
            with self.assertRaises(ValueError): self.preview()
        self.assertFalse(WRITES)

    def test_cancelled_work_call_rejected(self):
        STORE[('Overtime Work Call','CALL')].docstatus=2
        with self.assertRaisesRegex(ValueError,'submitted'): self.preview()

    def test_invalid_missing_and_overlapping_intervals(self):
        for rows in [[],[{}],[{'start':'bad','end':'bad'}],
                     [{'start':'2026-09-13 12:00','end':'2026-09-13 07:00'}],
                     self.args['intervals']*2,
                     [{'start':'2026-09-12 07:00','end':'2026-09-12 12:00'}],
                     [{'start':'2026-09-13 07:00','end':'2026-09-15 12:00'}]]:
            with self.subTest(rows=rows):
                self.args['intervals']=rows
                with self.assertRaises(ValueError): self.preview()

    def test_blank_reason_rejected(self):
        self.args['reason']=' '
        with self.assertRaisesRegex(ValueError,'reason'): self.preview()

    def test_breaks_excluded_and_partial_hours_calculated(self):
        self.args['intervals']=[{'start':'2026-09-13 07:30','end':'2026-09-13 09:00'},
                                {'start':'2026-09-13 09:30','end':'2026-09-13 12:00'}]
        p=self.preview(); self.assertEqual(p['snapshot']['verified_hours'],4)
        self.assertEqual(p['snapshot']['reconciliation_status'],'Partial')
        self.assertEqual(p['snapshot']['late_minutes'],30)

    def test_outside_window_hours_are_not_credited(self):
        self.args['intervals']=[{'start':'2026-09-13 06:00','end':'2026-09-13 13:00'}]
        p=self.preview(); self.assertEqual(p['snapshot']['verified_hours'],5)
        self.assertEqual(p['snapshot']['unapproved_hours'],2)
        self.assertEqual(p['snapshot']['reconciliation_status'],'Overrun')

    def test_approved_maximum_caps_hours(self):
        STORE[('Overtime Authorization','AUTH')].maximum_hours=3
        self.assertEqual(self.preview()['snapshot']['verified_hours'],3)

    def test_checkin_issues_do_not_override_manual_evidence(self):
        self.context['checkins']=[{'time':'2026-09-13 07:00','log_type':'IN'}]
        p=self.preview(); self.assertEqual(p['snapshot']['reconciliation_status'],'Completed')
        self.assertTrue(any('Open work' in w for w in p['checkin_comparison']['warnings']))
        self.assertEqual(len(p['checkin_comparison']['source_checkins']),1)

    def test_new_checkins_make_preview_stale(self):
        p=self.preview(); self.context['checkins']=[{'time':'2026-09-13 07:00','log_type':'IN'}]
        with self.assertRaisesRegex(ValueError,'new preview'): self.approve(p)
        self.assertFalse(WRITES)

    def test_setting_or_document_changes_make_preview_stale(self):
        p=self.preview(); SETTINGS.night_hours_rate=20
        with self.assertRaisesRegex(ValueError,'new preview'): self.approve(p)
        p=self.preview(); STORE[('Overtime Authorization','AUTH')].modified='new'
        with self.assertRaisesRegex(ValueError,'new preview'): self.approve(p)

    def test_duplicate_confirmation_is_rejected(self):
        p=self.preview(); self.approve(p)
        with self.assertRaisesRegex(ValueError,'new preview'): self.approve(p)
        self.assertEqual(len(WRITES),2)

    def test_settlement_after_preview_blocks_approval(self):
        p=self.preview(); STORE[('Overtime Authorization','AUTH')].settlement_status='Credited'
        with self.assertRaises(ValueError): self.approve(p)
        self.assertFalse(WRITES)

    def test_manual_snapshot_survives_work_call_refresh(self):
        self.approve(); before=get_doc('Overtime Authorization','AUTH'); WRITES.clear()
        with patch.object(calls,'reconcile_overtime_document',side_effect=AssertionError('Must preserve manual evidence')):
            result=calls.reconcile_overtime_work_call('CALL',dry_run=0)
        self.assertEqual(result['verified_hours'],5)
        self.assertEqual(get_doc('Overtime Authorization','AUTH'),before)
        self.assertTrue(all(w[0]=='Overtime Work Call' for w in WRITES))

    def test_confirmation_uses_current_reads_for_settings_and_calculation(self):
        p=self.preview()
        with patch.object(service, '_reconcile', wraps=service._reconcile) as calculate:
            self.approve(p)
        self.assertTrue(all(call.kwargs['for_update'] for call in calculate.call_args_list))
        self.assertIn(('DGII Payroll Settings', 'DGII Payroll Settings'), LOCKS)
        self.assertIn(('Overtime Authorization', 'rows'), LOCKS)

    def test_current_read_bypasses_repeatable_read_snapshot(self):
        with patch.object(frappe, 'get_all', return_value=['stale']), \
             patch.object(frappe.db, 'get_values', return_value=[Record(name='current')]) as current:
            self.assertEqual(overtime._reconciliation_rows('Employee Checkin', pluck='name'), ['stale'])
            self.assertEqual(overtime._reconciliation_rows('Employee Checkin', pluck='name', for_update=True), ['current'])
            self.assertTrue(current.call_args.kwargs['for_update'])

    def test_refresh_uses_current_manual_source_after_waiting_for_lock(self):
        old=get_doc('Overtime Authorization','AUTH')
        self.approve(); WRITES.clear()
        def read(dt, name, **kwargs):
            if dt == 'Overtime Authorization' and not kwargs.get('for_update'):
                return old
            return get_doc(dt, name, **kwargs)
        with patch.object(frappe,'get_doc',side_effect=read), \
             patch.object(calls,'reconcile_overtime_document',side_effect=AssertionError('Stale source')):
            calls.reconcile_overtime_work_call('CALL',dry_run=0)
        self.assertTrue(all(write[0]=='Overtime Work Call' for write in WRITES))

    def test_standalone_approval_and_checkin_overwrite_guard(self):
        STORE[('Overtime Authorization','AUTH')].overtime_work_call=None
        self.approve(); WRITES.clear()
        with self.assertRaisesRegex(ValueError,'manually verified'):
            overtime.save_authorization_reconciliation('AUTH')
        self.assertFalse(WRITES)

    def test_regular_shift_is_excluded_and_weekly_split_preserved(self):
        self.context.update(classification='Regular Workday',shift_start='2026-09-13 07:00',shift_end='2026-09-13 10:00')
        self.context['warnings']=[]
        with patch.object(overtime,'_get_verified_regular_overtime_before',return_value=23):
            p=self.preview()
        self.assertEqual(p['snapshot']['verified_hours'],2)
        self.assertEqual(p['snapshot']['regular_35_hours'],1)
        self.assertEqual(p['snapshot']['regular_100_hours'],1)

    def test_later_weekly_snapshot_blocks_reclassification(self):
        self.context.update(classification='Regular Workday',shift_start='2026-09-13 01:00',shift_end='2026-09-13 06:00')
        auth('LATER',authorization_start='2026-09-13 13:00:00',verified_hours=3,regular_35_hours=3)
        with self.assertRaisesRegex(ValueError,'chronologically'): self.preview()

    def test_zero_overtime_is_not_certified(self):
        self.context.update(classification='Regular Workday',shift_start='2026-09-13 07:00',shift_end='2026-09-13 12:00')
        with self.assertRaisesRegex(ValueError,'no eligible'): self.preview()

    def test_holiday_and_night_classification(self):
        self.context.update(classification='Legal Holiday')
        auth(authorization_start='2026-09-12 21:00:00',authorization_end='2026-09-13 02:00:00')
        self.args['intervals']=[{'start':'2026-09-12 21:00','end':'2026-09-13 02:00'}]
        p=self.preview(); self.assertEqual(p['snapshot']['holiday_100_hours'],5)
        self.assertEqual(p['snapshot']['night_hours'],5)

    def test_amendment_retains_previous_snapshot_in_audit(self):
        self.approve(); self.args['intervals']=[{'start':'2026-09-13 08:00','end':'2026-09-13 12:00'}]
        self.args['reason']='Corrected arrival after supervisor review'; self.approve()
        self.assertEqual(get_doc('Overtime Authorization','AUTH').verified_hours,4)
        self.assertIn('&quot;verified_hours&quot;: 5.0', COMMENTS[2][2])

    def test_new_or_draft_document_cannot_inject_manual_evidence(self):
        for before in (None, Record(docstatus=0)):
            doc=auth(docstatus=0, reconciliation_source='Manual Verification', before=before)
            with self.assertRaisesRegex(ValueError,'Manual Attendance Verification'):
                service.protect_manual_snapshot(doc)

    def test_generic_document_save_cannot_forge_manual_evidence(self):
        doc=auth(); doc.before=Record(copy.deepcopy(doc)); doc.reconciliation_source='Manual Verification'
        with self.assertRaisesRegex(ValueError,'Manual Attendance Verification'):
            OvertimeAuthorization.before_update_after_submit(doc)

    def test_generic_document_save_cannot_amend_manual_snapshot(self):
        self.approve(); doc=get_doc('Overtime Authorization','AUTH'); doc.before=Record(copy.deepcopy(doc)); doc.verified_hours=100
        with self.assertRaises(ValueError): OvertimeAuthorization.before_update_after_submit(doc)

    def test_reason_is_escaped_in_audit(self):
        self.args['reason']='<script>alert(1)</script>'; self.approve()
        self.assertTrue(all('<script>' not in text for _,_,text in COMMENTS))

    def test_options_hide_button_for_disallowed_roles(self):
        ROLES[:]=['HR User']
        self.assertFalse(service.get_manual_verification_options(work_call='CALL')['allowed'])

    def test_settings_require_explicit_valid_roles(self):
        for roles in ['', 'All', 'Guest', 'Unknown Role']:
            SETTINGS.overtime_manual_verification_roles=roles
            with self.assertRaises(ValueError): DGIIPayrollSettings.validate(SETTINGS)
        SETTINGS.overtime_manual_verification_roles='Custom Approver\nSystem Manager'
        DGIIPayrollSettings.validate(SETTINGS)

    def test_manual_hours_are_counted_in_later_weekly_calculation(self):
        earlier=auth('EARLY',work_date='2026-09-12',authorization_start='2026-09-12 07:00:00',
                     reconciliation_source='Manual Verification',regular_35_hours=4,regular_100_hours=1,verified_hours=5)
        # Bypass only the setUp patch for this targeted real weekly-helper test.
        self.patches[1].stop()
        with patch.object(overtime,'_get_context',side_effect=AssertionError('Must use saved manual totals')):
            self.assertEqual(overtime._get_verified_regular_overtime_before(get_doc('Overtime Authorization','AUTH')),5)

if __name__ == '__main__': unittest.main()
