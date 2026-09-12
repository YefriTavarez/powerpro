"""Site-free contract tests of the calendar calculator and read-only service."""
import copy
from datetime import date, datetime, timedelta
import importlib
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
pkg = types.ModuleType("powerpro")
pkg.__path__ = [str(ROOT / "powerpro")]
sys.modules["powerpro"] = pkg
rules = importlib.import_module("powerpro.payroll_rules.overtime_calendar")
legacy = importlib.import_module("powerpro.payroll_rules.overtime")


def dt(value): return datetime.fromisoformat(str(value))
def context(day, classification=legacy.REGULAR_DAY, start="08:00:00", end="18:00:00"):
    day = date.fromisoformat(str(day))
    a, b = dt(f"{day}T{start}"), dt(f"{day}T{end}")
    if b <= a: b += timedelta(days=1)
    return dict(date=str(day), classification=classification, shift_start=a, shift_end=b,
                holiday_list_covers_work_date=True, warnings=[])


class CalculatorTest(unittest.TestCase):
    def calculate(self, start="2026-09-23T22:00:00", end="2026-09-24T02:00:00", **overrides):
        args = dict(authorization_start=start, authorization_end=end, maximum_hours=4,
                    intervals=[legacy.WorkInterval(dt(start), dt(end))],
                    contexts=[context("2026-09-23"), context("2026-09-24", legacy.LEGAL_HOLIDAY)])
        args.update(overrides)
        return rules.reconcile_calendar_intervals(**args)

    def test_enter_holiday(self):
        x = self.calculate()
        self.assertEqual((x['regular_35_hours'], x['holiday_100_hours'], x['night_hours']), (2, 2, 4))
        self.assertEqual([s['date'] for s in x['segments']], ['2026-09-23', '2026-09-24'])

    def test_exit_holiday(self):
        x = self.calculate(contexts=[context('2026-09-23', legacy.LEGAL_HOLIDAY), context('2026-09-24')])
        self.assertEqual((x['regular_35_hours'], x['holiday_100_hours']), (2, 2))

    def test_global_cap_is_not_restarted_at_midnight(self):
        x = self.calculate(maximum_hours=3)
        self.assertEqual((x['regular_35_hours'], x['holiday_100_hours'], x['verified_hours']), (2, 1, 3))
        self.assertEqual(x['segments'][-1]['end'], '2026-09-24T01:00:00')
        self.assertEqual(x['excluded_by_maximum_hours'], 1)

    def test_midnight_end_does_not_require_following_calendar(self):
        x = self.calculate(end='2026-09-24T00:00:00', contexts=[context('2026-09-23')])
        self.assertEqual(x['verified_hours'], 2)

    def test_missing_next_day_calendar_fails(self):
        with self.assertRaisesRegex(ValueError, 'calendario'):
            self.calculate(contexts=[context('2026-09-23')])

    def test_breaks_are_not_filled(self):
        x = self.calculate(intervals=[legacy.WorkInterval(dt('2026-09-23T22:00:00'), dt('2026-09-23T23:00:00')),
                                     legacy.WorkInterval(dt('2026-09-24T00:00:00'), dt('2026-09-24T02:00:00'))])
        self.assertEqual((x['verified_hours'], x['night_hours']), (3, 3))

    def test_no_evidence_creates_no_hours(self):
        self.assertEqual(self.calculate(intervals=[])['verified_hours'], 0)

    def test_ordinary_next_day_shift_is_excluded(self):
        x = self.calculate(start='2026-09-23T23:00:00', end='2026-09-24T10:00:00', maximum_hours=20,
                           contexts=[context('2026-09-23'), context('2026-09-24')])
        self.assertEqual(x['verified_hours'], 9)

    def test_previous_night_shift_is_excluded(self):
        x = self.calculate(start='2026-09-24T00:00:00', end='2026-09-24T07:00:00', maximum_hours=7,
                           contexts=[context('2026-09-23', start='22:00:00', end='06:00:00'),
                                     context('2026-09-24', start='22:00:00', end='06:00:00')])
        self.assertEqual(x['verified_hours'], 1)
        self.assertEqual(x['segments'][0]['start'], '2026-09-24T06:00:00')

    def test_weekly_band_resets_without_carrying_sunday_hours_into_monday(self):
        x = self.calculate(start='2026-09-27T23:00:00', end='2026-09-28T02:00:00',
                           contexts=[context('2026-09-27'), context('2026-09-28')],
                           regular_hours_before_by_week={'2026-09-21': 24, '2026-09-28': 0})
        self.assertEqual((x['regular_35_hours'], x['regular_100_hours']), (2, 1))

    def test_weekly_rest_remains_separate(self):
        x = self.calculate(contexts=[context('2026-09-23'), context('2026-09-24', legacy.WEEKLY_REST)])
        self.assertEqual((x['weekly_rest_hours'], x['holiday_100_hours']), (2, 0))

    def test_night_boundaries_and_seconds(self):
        x = self.calculate(start='2026-09-23T20:59:59', end='2026-09-23T21:00:01', maximum_hours=1)
        self.assertEqual(x['night_hours'], .0003)
        x = self.calculate(start='2026-09-24T06:59:59', end='2026-09-24T07:00:01', maximum_hours=1)
        self.assertEqual(x['night_hours'], .0003)

    def test_example_has_no_regression(self):
        x = self.calculate(start='2026-09-23T18:00:00', end='2026-09-23T21:35:24', maximum_hours=3.59)
        self.assertEqual((x['verified_hours'], x['night_hours']), (3.59, .59))

    def test_rejects_overlap_nonfinite_and_long_windows(self):
        for value in [0, -1, float('nan'), float('inf')]:
            with self.subTest(value=value), self.assertRaises(ValueError): self.calculate(maximum_hours=value)
        pair = legacy.WorkInterval(dt('2026-09-23T22:00:00'), dt('2026-09-24T02:00:00'))
        with self.assertRaises(ValueError): self.calculate(intervals=[pair, pair])
        with self.assertRaises(ValueError): self.calculate(end='2026-09-26T02:00:00')


class Record(dict):
    def __getattr__(self, key):
        if key.startswith('__'): raise AttributeError(key)
        return self.get(key)
    def __setattr__(self, key, value): self[key] = value
    def as_dict(self): return dict(self)
    def check_permission(self, action):
        if self.get('denied'): raise PermissionError('Denied')


def throw(message, exc=ValueError): raise exc(message)
frappe = types.ModuleType('frappe')
frappe.whitelist = lambda: lambda f: f
frappe._ = lambda x: x
frappe._dict = Record
frappe.throw = throw
frappe.ValidationError = ValueError
import json
frappe.parse_json = lambda x: json.loads(x) if isinstance(x, str) else x
frappe.get_doc = lambda *args: None
frappe.get_single = lambda *args: None
frappe.get_list = lambda *args, **kwargs: []
frappe.get_all = lambda *args, **kwargs: []
frappe.has_permission = lambda *args, **kwargs: False
frappe.db = Record(get_value=lambda *args: 'DOP')
sys.modules['frappe'] = frappe
utils = types.ModuleType('frappe.utils')
utils.flt = lambda x: float(x or 0)
utils.get_datetime = dt
utils.now_datetime = lambda: dt("2026-09-30")
utils.getdate = lambda x: date.fromisoformat(str(x)[:10])
sys.modules['frappe.utils'] = utils
adapter = types.ModuleType('powerpro.controllers.overtime')
adapter._get_checkins = lambda *args: []
adapter._get_verified_regular_overtime_before = lambda doc: 0
adapter.get_schedule_context = lambda day, *args: context(day, legacy.LEGAL_HOLIDAY if str(day) == '2026-09-24' else legacy.REGULAR_DAY)
sys.modules[adapter.__name__] = adapter
service = importlib.import_module('powerpro.controllers.overtime_calendar')


class ServiceTest(unittest.TestCase):
    def setUp(self):
        self.doc = Record(doctype='Overtime Authorization', name='AUTH-TEST', employee='TEST', employee_name='Test',
                          company='Test', docstatus=1, work_date='2026-09-23', shift_type='Test', holiday_list='2026',
                          authorization_start='2026-09-23T22:00:00', authorization_end='2026-09-24T02:00:00',
                          maximum_hours=4, modified='2026-09-25', reconciled_on='2026-09-25',
                          source_checkins=json.dumps([{'time':'2026-09-23T22:00:00','log_type':'IN'},
                                                     {'time':'2026-09-24T02:00:00','log_type':'OUT'}]))
        self.settings = Record(weekly_expected_hours=44,max_weekly_extra_hours=68,start_night_hours='21:00:00',
                               end_night_hours='07:00:00',extra_hours_rate=35,extraordinary_hours_rate=100,night_hours_rate=15)
        self.stack = __import__('contextlib').ExitStack()
        self.stack.enter_context(patch.object(frappe, 'get_doc', return_value=self.doc))
        self.stack.enter_context(patch.object(frappe, 'get_single', return_value=self.settings))
        self.addCleanup(self.stack.close)

    def compare(self): return service.get_calendar_comparison(self.doc.doctype, self.doc.name)

    def test_denied_document_stops_before_evidence(self):
        self.doc.denied = True
        with patch.object(service, '_evidence') as evidence:
            with self.assertRaises(PermissionError): self.compare()
            evidence.assert_not_called()

    def test_arbitrary_doctype_is_rejected(self):
        with self.assertRaises(ValueError): service.get_calendar_comparison('User','Administrator')

    def test_snapshot_evidence_is_not_replaced_by_live_punches(self):
        before = copy.deepcopy(self.doc)
        with patch.object(service, '_get_checkins', side_effect=AssertionError('Must use saved evidence')):
            x = self.compare()
        self.assertEqual(x['baseline']['regular_35_hours'], 4)
        self.assertEqual(x['proposed']['holiday_100_hours'], 2)
        self.assertEqual(x['difference']['regular_35_hours'], -2)
        self.assertEqual(self.doc, before)
        self.assertEqual(x['saved_documents'], 0)
        self.assertFalse(x['settlement_enabled'])
        self.assertIsNone(x['pricing'])

    def test_saved_snapshot_without_evidence_is_rejected(self):
        self.doc.source_checkins = '[]'
        with self.assertRaisesRegex(ValueError, 'instantánea'): self.compare()

    def test_presumed_attendance_is_not_labelled_verified(self):
        self.doc.reconciliation_source = 'Presumed Attendance'
        with self.assertRaisesRegex(ValueError, 'presumida'): self.compare()

    def test_manual_verification_is_preserved(self):
        self.doc.reconciliation_source = 'Manual Verification'
        self.doc.manual_worked_intervals = json.dumps([{'start':self.doc.authorization_start,'end':self.doc.authorization_end}])
        x = self.compare()
        self.assertEqual(x['evidence_source'], 'Verificación manual guardada')
        self.assertEqual(x['proposed']['verified_hours'], 4)

    def test_illustrative_pricing_uses_already_visible_snapshot_rate(self):
        self.doc.settlement_hourly_rate = 100
        x = self.compare()
        self.assertEqual(x['pricing']['baseline']['total_amount'], 600)
        self.assertEqual(x['pricing']['proposed']['total_amount'], 730)
        self.assertEqual(x['pricing']['difference'], 130)

    def test_missing_live_evidence_is_an_explanation_not_an_absence(self):
        self.doc.reconciled_on = None
        x = self.compare()
        self.assertEqual(x['proposed']['verified_hours'], 0)
        self.assertTrue(any('No hay marcaciones' in w for w in x['warnings']))
        self.assertNotIn('reconciliation_status', x)

    def test_repeat_is_deterministic(self):
        self.assertEqual(self.compare(), self.compare())

    def test_salary_values_are_not_returned_without_document_permission(self):
        salary = Record(doctype='Salary Structure Assignment', name='SALARY', salary_per_hour=999)
        def permission(doctype, action, doc=None): return doc is None
        def get_doc(doctype, name): return salary if doctype == salary.doctype else self.doc
        with patch.object(frappe, 'has_permission', side_effect=permission), \
             patch.object(frappe, 'get_all', return_value=[Record(name='SALARY')]), \
             patch.object(frappe, 'get_doc', side_effect=get_doc):
            x = self.compare()
        self.assertIsNone(x['pricing'])
        self.assertNotIn('999', json.dumps(x, default=str))

    def test_accessible_effective_salary_is_used(self):
        salary = Record(doctype='Salary Structure Assignment', name='SALARY', salary_per_hour=100)
        def get_doc(doctype, name): return salary if doctype == salary.doctype else self.doc
        with patch.object(frappe, 'has_permission', return_value=True), \
             patch.object(frappe, 'get_all', return_value=[Record(name='SALARY')]), \
             patch.object(frappe, 'get_doc', side_effect=get_doc):
            x = self.compare()
        self.assertEqual(x['pricing']['proposed']['total_amount'], 730)

    def test_no_salary_is_a_note_not_a_failed_hour_comparison(self):
        with patch.object(frappe, 'has_permission', return_value=True): x = self.compare()
        self.assertIsNone(x['pricing'])
        self.assertEqual(x['proposed']['holiday_100_hours'], 2)

    def test_work_call_options_use_permission_filtered_list(self):
        with patch.object(frappe, 'get_list', return_value=[]) as query:
            service.get_work_call_comparison_options(self.doc.name)
            self.assertEqual(query.call_args.kwargs['filters']['overtime_work_call'], self.doc.name)


if __name__ == '__main__': unittest.main()
