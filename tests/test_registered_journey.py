import copy
import unittest
from datetime import datetime
from powerpro.payroll_rules.registered_journey import declared_session
from powerpro.payroll_rules.ordinary_night import evaluate_night_work


class RegisteredJourneyTest(unittest.TestCase):
    def setUp(self):
        self.record = dict(name='JORN-TEST', starts_at='2026-09-18 18:00:00', ends_at='2026-09-19 06:00:00')
        self.row = dict(break_mode='Descanso Declarado', actual_start=self.record['starts_at'],
            actual_end=self.record['ends_at'], break_start='2026-09-18 23:00:00',
            break_end='2026-09-19 00:00:00', evidence_reference='Declaración revisada')
        self.lower = datetime(2026, 9, 18, 18)
        self.upper = datetime(2026, 9, 19, 6)
        self.now = datetime(2026, 10, 15)

    def declaration(self):
        return declared_session(self.record, self.row, self.lower, self.upper, self.now)

    def test_ordinary_night_only_pays_premium_and_excludes_declared_break(self):
        declaration = self.declaration()
        punches = [dict(name='TEST-IN', time=self.record['starts_at'], log_type='IN', shift='Old')]
        before = copy.deepcopy(punches)
        result = evaluate_night_work(rows=punches, shift=dict(name='Night'),
            context=dict(shift_start=self.lower, shift_end=self.upper,
                         classification='Regular Workday', holiday_list_covers_work_date=True),
            extensions=[], next_windows=[], now=self.now, basis='Clock overlap',
            certified_intervals=declaration['intervals'])
        self.assertEqual(result['state'], 'Verified')
        self.assertEqual(result['night_session']['ordinary_premium_hours'], 8)
        self.assertEqual(result['night_session']['overtime_premium_hours'], 0)
        self.assertEqual(punches, before)
        self.assertEqual(result['source_checkins'], before)

    def test_break_location_changes_premium_without_changing_total_work(self):
        self.row.update(break_start='2026-09-18 19:00:00', break_end='2026-09-18 20:00:00')
        declaration = self.declaration()
        result = evaluate_night_work(rows=[], shift=dict(name='Night'),
            context=dict(shift_start=self.lower, shift_end=self.upper,
                         classification='Regular Workday', holiday_list_covers_work_date=True),
            extensions=[], next_windows=[], now=self.now, basis='Clock overlap',
            certified_intervals=declaration['intervals'])
        self.assertEqual(result['night_session']['ordinary_premium_hours'], 9)

    def test_unlocated_flexible_break_requires_a_rule(self):
        self.row['break_mode'] = 'Descanso Flexible del Turno'
        with self.assertRaisesRegex(ValueError, 'regla aprobada'):
            self.declaration()

    def test_raw_punch_mode_does_not_invent_a_declaration(self):
        self.row['break_mode'] = 'Marcaciones'
        self.assertIsNone(self.declaration())

    def test_missing_reference_future_window_and_invalid_break_fail(self):
        for changes in [dict(evidence_reference=''), dict(break_end='2026-09-20'),
                        dict(break_end=self.row['break_start']), dict(actual_start='2026-09-18 17:00:00')]:
            row = {**self.row, **changes}
            with self.assertRaises(ValueError):
                declared_session(self.record, row, self.lower, self.upper, self.now)
        with self.assertRaisesRegex(ValueError, 'terminado'):
            declared_session(self.record, self.row, self.lower, self.upper, self.lower)

    def test_outside_native_ordinary_window_requires_an_authorized_extension(self):
        self.record['ends_at'] = self.row['actual_end'] = '2026-09-19 07:00:00'
        with self.assertRaisesRegex(ValueError, 'dentro'):
            self.declaration()


if __name__ == '__main__':
    unittest.main()
