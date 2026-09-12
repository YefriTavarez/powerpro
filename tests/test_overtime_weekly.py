"""Run directly; no Frappe site, fixtures, or business writes."""
import unittest
from unittest.mock import patch
from test_overtime_calendar import Record, frappe
from powerpro.payroll_rules.overtime_weekly import reconstruct_week
from powerpro.controllers.overtime_weekly import get_weekly_evidence, LIMIT


def punch(stamp, kind, name=None):
    return dict(time=stamp, log_type=kind, name=name or stamp + kind)


def pair(day, start='08:00', end='16:00'):
    return [punch(f'2026-09-{day}T{start}', 'IN'), punch(f'2026-09-{day}T{end}', 'OUT')]


class WeeklyTest(unittest.TestCase):
    def calc(self, rows, **kw):
        args = dict(week_start='2026-09-21', cutoff='2026-09-23T18:00', checkins=rows)
        args.update(kw)
        return reconstruct_week(**args)

    def test_ordinary_hours_not_assumed_44(self):
        x = self.calc(pair(21) + pair(22))
        self.assertEqual(x['hours_before_cutoff'], 16)
        self.assertEqual(x['provisional_hours_to_threshold'], 52)
        self.assertFalse(x['complete']); self.assertFalse(x['settlement_eligible'])

    def test_all_calendar_days_count_without_premium_classification(self):
        x = self.calc(pair(24) + pair(27))
        self.assertEqual(x['paired_hours'], 16)
        self.assertEqual(x['hours_before_cutoff'], 0)

    def test_breaks_excluded_and_cutoff_splits_interval(self):
        x = self.calc(pair(23, '08:00', '12:00') + pair(23, '13:00', '20:00'))
        self.assertEqual((x['paired_hours'], x['hours_before_cutoff']), (11, 9))

    def test_in_in_out_does_not_invent_work(self):
        x = self.calc([punch('2026-09-21T08:00','IN'), punch('2026-09-21T12:00','IN'), punch('2026-09-21T17:00','OUT')])
        self.assertEqual(x['paired_hours'], 0)
        self.assertIn('consecutive_in', [i['code'] for i in x['issues']])

    def test_clean_pair_after_ambiguous_pair_is_retained(self):
        x = self.calc([punch('2026-09-21T05:00','IN'), punch('2026-09-21T06:00','IN'), punch('2026-09-21T07:00','OUT')] + pair(21))
        self.assertEqual(x['paired_hours'], 8)

    def test_overnight_split_by_date_and_week(self):
        rows = [punch('2026-09-20T22:00','IN'), punch('2026-09-21T06:00','OUT'),
                punch('2026-09-27T22:00','IN'), punch('2026-09-28T06:00','OUT')]
        x = self.calc(rows)
        self.assertEqual(x['paired_hours'], 8)
        self.assertEqual(x['days'][0]['paired_hours'], 6)
        self.assertEqual(x['days'][-1]['paired_hours'], 2)
        following = self.calc(rows, week_start='2026-09-28', cutoff='2026-09-28T07:00')
        self.assertEqual(following['paired_hours'], 6)

    def test_missing_marks_do_not_become_attendance(self):
        for rows in [[], [punch('2026-09-21T08:00','IN')], [punch('2026-09-21T17:00','OUT')]]:
            x = self.calc(rows)
            self.assertEqual(x['paired_hours'], 0)
            self.assertNotIn('attendance_status', x)
            self.assertFalse(x['complete'])

    def test_duplicate_timestamp_cannot_be_paired(self):
        x = self.calc(pair(21) + [punch('2026-09-21T08:00','OUT','DUP')])
        self.assertEqual(x['paired_hours'], 0)
        self.assertIn('duplicate_timestamp', [i['code'] for i in x['issues']])

    def test_unknown_type_taints_open_pair(self):
        x = self.calc(pair(21) + [punch('2026-09-21T09:00','')])
        self.assertEqual(x['paired_hours'], 0)

    def test_over_24_hour_pair_requires_review(self):
        x = self.calc([punch('2026-09-21T08:00','IN'), punch('2026-09-22T09:00','OUT')])
        self.assertEqual(x['paired_hours'], 0)
        self.assertIn('invalid_duration', [i['code'] for i in x['issues']])

    def test_threshold_uses_total_and_never_goes_negative(self):
        x = self.calc(pair(21) + pair(22), threshold=12)
        self.assertEqual(x['provisional_hours_to_threshold'], 0)

    def test_deterministic_and_validated(self):
        self.assertEqual(self.calc(pair(21)), self.calc(list(reversed(pair(21)))))
        for v in [0, -1, float('inf'), float('nan')]:
            with self.assertRaises(ValueError): self.calc([], threshold=v)
        with self.assertRaises(ValueError): self.calc([], week_start='2026-09-22')


class AdapterTest(unittest.TestCase):
    doc = Record(employee='EMP-TEST', authorization_start='2026-09-23T18:00')
    def test_denied_does_not_read_rows(self):
        with patch.object(frappe, 'has_permission', return_value=False), patch.object(frappe, 'get_list') as query:
            self.assertFalse(get_weekly_evidence(self.doc, {'2026-09-21':0}, 68)['available'])
            query.assert_not_called()

    def test_permission_filtered_query_is_bounded_and_scoped(self):
        with patch.object(frappe, 'has_permission', return_value=True), patch.object(frappe, 'get_list', return_value=pair(21)) as query:
            x = get_weekly_evidence(self.doc, {'2026-09-21':3}, 68)
            args = query.call_args.kwargs
            self.assertEqual(args['limit_page_length'], LIMIT + 1)
            self.assertIn(['employee', '=', 'EMP-TEST'], args['filters'])
            self.assertEqual(x['weeks'][0]['paired_hours'], 8)
            self.assertEqual(x['weeks'][0]['legacy_regular_overtime_before'], 3)
            self.assertFalse(x['weeks'][0]['complete'])

    def test_truncated_evidence_is_not_calculated(self):
        with patch.object(frappe, 'has_permission', return_value=True), patch.object(frappe, 'get_list', return_value=[{}] * (LIMIT+1)):
            week = get_weekly_evidence(self.doc, {'2026-09-21':0}, 68)['weeks'][0]
            self.assertTrue(week['truncated'])
            self.assertNotIn('paired_hours', week)

    def test_changed_evidence_changes_digest(self):
        with patch.object(frappe, 'has_permission', return_value=True), patch.object(frappe, 'get_list', return_value=pair(21)):
            a = get_weekly_evidence(self.doc, {'2026-09-21':0}, 68)
        with patch.object(frappe, 'has_permission', return_value=True), patch.object(frappe, 'get_list', return_value=pair(22)):
            b = get_weekly_evidence(self.doc, {'2026-09-21':0}, 68)
        self.assertNotEqual(a['weeks'][0]['source_hash'], b['weeks'][0]['source_hash'])


if __name__ == '__main__': unittest.main()
