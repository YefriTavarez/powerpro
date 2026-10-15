"""Contract tests for the optional adapter; no site or business records needed."""
import importlib.util
import json
import sys
import types
import unittest
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from unittest.mock import patch


class Record(dict):
    def __getattr__(self, key):
        if key.startswith('__'):
            raise AttributeError(key)
        return self.get(key)
    def check_permission(self, action):
        if self.get('denied'):
            raise PermissionError('denied')
    def as_dict(self):
        return dict(self)


class AssignmentHistoryTest(unittest.TestCase):
    def setUp(self):
        self.row = Record(name='SHA', employee='EMP', shift_type='Night', start_date='2026-09-18',
            end_date='2026-09-18', docstatus=1, status='Active', modified='2026-09-18',
            custom_igc_journey='JORN', custom_igc_journey_row='ROW', custom_igc_journey_key='JORN|ROW')
        self.record = Record(name='JORN', starts_at='2026-09-18 18:00', replacement_shift='Night',
            journey_type='Cambio de Turno', employees=[Record(name='ROW', employee='EMP', shift_assignment='SHA')])
        self.rows = [self.row]
        self.managed = True
        self.calls = []
        def get_rows(dt, **kw):
            self.calls.append(kw)
            f = kw['filters']
            return [Record(deepcopy(r)) for r in self.rows if r.docstatus == f['docstatus']
                    and ((r.status == 'Active') if f['status'] == 'Active' else (r.status != 'Active' and r.custom_igc_journey))]
        def throw(message):
            raise ValueError(message)
        frappe = types.ModuleType('frappe')
        frappe.whitelist = lambda: lambda f: f
        frappe.throw = throw
        frappe.get_meta = lambda dt: Record(has_field=lambda field: self.managed)
        frappe.get_doc = lambda *a, **kw: self.record
        utils = types.ModuleType('frappe.utils')
        utils.getdate = lambda value: datetime.fromisoformat(str(value)).date()
        utils.get_datetime = lambda value: datetime.fromisoformat(str(value))
        utils.now_datetime = lambda: datetime(2026, 10, 15)
        overtime = types.ModuleType('powerpro.controllers.overtime')
        overtime._reconciliation_rows = get_rows
        self.patch = patch.dict(sys.modules, {'frappe': frappe, 'frappe.utils': utils,
                                             'powerpro.controllers.overtime': overtime})
        self.patch.start()
        self.addCleanup(self.patch.stop)
        spec = importlib.util.spec_from_file_location('journey_adapter_under_test',
            Path(__file__).resolve().parents[1] / 'powerpro/controllers/registered_journey.py')
        self.adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.adapter)

    def load(self):
        return self.adapter.shift_assignments('EMP', '2026-09-19', for_update=True, include_modified=True)

    def test_scheduler_expiry_does_not_change_historical_evidence(self):
        before = self.load()
        self.row.update(status='Inactive', modified='2026-10-15')
        self.assertEqual(self.load(), before)
        self.assertNotIn('modified', before[0])
        self.assertTrue(all(call['for_update'] for call in self.calls))

    def test_cancellation_removes_the_assignment(self):
        self.row['docstatus'] = 2
        self.assertEqual(self.load(), [])

    def test_unmanaged_inactive_assignment_is_not_reactivated(self):
        self.row.update(status='Inactive', custom_igc_journey=None)
        self.assertEqual(self.load(), [])

    def test_bad_link_or_changed_shift_is_rejected(self):
        self.record['replacement_shift'] = 'Day'
        with self.assertRaisesRegex(ValueError, 'no coincide'):
            self.load()

    def test_record_permission_is_required(self):
        self.record['denied'] = True
        with self.assertRaises(PermissionError):
            self.load()

    def test_sites_without_registration_fields_keep_active_query(self):
        self.managed = False
        self.load()
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0]['filters']['status'], 'Active')

    def test_approved_ordinary_declaration_contributes_to_later_week(self):
        evidence = {'state': 'Verified', 'input_hash': 'same',
            'worked_intervals': [{'start': '2026-09-18T18:00:00', 'end': '2026-09-18T23:00:00'}],
            'source_checkins': [{'name': 'IN'}],
            'input': {'certified_session': {'registration': 'JORN'}, 'shift': {'name': 'Night'},
                      'context': {'shift_start': '2026-09-18 18:00:00', 'shift_end': '2026-09-19 06:00:00'}}}
        frappe = sys.modules['frappe']
        frappe.db = Record(exists=lambda *args: True)
        frappe.parse_json = json.loads
        frappe.ValidationError = ValueError
        frappe.get_doc = lambda *a, **kw: Record(name='ONS', evidence_snapshot=json.dumps(evidence))
        sys.modules['powerpro.controllers.overtime']._reconciliation_rows = lambda *a, **kw: ['ONS']
        night = types.ModuleType('powerpro.controllers.ordinary_night')
        night.build_preview = lambda *a, **kw: evidence
        checkin = types.ModuleType('powerpro.controllers.checkin_overtime')
        checkin._evidence_hash = lambda value: json.dumps(value, sort_keys=True)
        with patch.dict(sys.modules, {night.__name__: night, checkin.__name__: checkin}):
            result = self.adapter.ordinary_week_evidence('EMP', '2026-09-14', '2026-09-20', for_update=True)
            self.assertEqual(result['intervals'], evidence['worked_intervals'])
            self.assertEqual(result['checkins'], ['IN'])
            self.assertEqual(result['sessions'][0]['shift'], 'Night')
            self.assertEqual(result['issues'], [])
            night.build_preview = lambda *a, **kw: {**evidence, 'input_hash': 'changed'}
            changed = self.adapter.ordinary_week_evidence('EMP', '2026-09-14', '2026-09-20', for_update=True)
            self.assertEqual(changed['intervals'], [])
            self.assertEqual(changed['issues'][0]['code'], 'weekly_previous_snapshot_changed')


if __name__ == '__main__':
    unittest.main()
