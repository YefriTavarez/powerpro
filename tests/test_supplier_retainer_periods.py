"""Calendar/idempotency contracts runnable without a Frappe bench."""
from datetime import date, datetime
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('retainer_periods', ROOT / 'powerpro/retainers/periods.py')
periods = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(periods)


class RetainerPeriodTest(unittest.TestCase):
    def test_month_dates_canonicalize_to_one_period(self):
        expected = (date(2026, 9, 1), date(2026, 9, 30))
        for day in (1, 2, 15, 16, 29, 30):
            self.assertEqual(periods.period_bounds(date(2026, 9, day), 'Monthly'), expected)

    def test_calendar_halves_are_disjoint_and_cover_the_month(self):
        for year, month in ((2026, 2), (2028, 2), (2026, 4), (2026, 12)):
            whole = periods.period_bounds(date(year, month, 1), 'Monthly')
            early = periods.period_bounds(date(year, month, 15), 'Bimonthly')
            late = periods.period_bounds(date(year, month, 16), 'Bimonthly')
            self.assertEqual((early[0], late[1]), whole)
            self.assertEqual((late[0] - early[1]).days, 1)
            self.assertEqual(early[1].day, 15)

    def test_leap_year_february_end(self):
        self.assertEqual(periods.period_bounds('2028-02-25', 'Monthly')[1], date(2028, 2, 29))
        self.assertEqual(periods.period_bounds('2026-02-25', 'Monthly')[1], date(2026, 2, 28))

    def test_datetime_and_string_have_same_period(self):
        self.assertEqual(periods.period_bounds(datetime(2026, 9, 15, 23, 59), 'Monthly'),
                         periods.period_bounds('2026-09-15', 'Monthly'))

    def test_unknown_frequency_and_invalid_date_rejected(self):
        for frequency in ('Weekly', '', None, 'monthly'):
            with self.assertRaises(ValueError):
                periods.period_bounds('2026-09-15', frequency)
        with self.assertRaises(ValueError):
            periods.period_bounds('2026-02-31', 'Monthly')

    def test_key_stable_for_canonical_period_and_separate_agreements(self):
        one = periods.period_bounds('2026-09-01', 'Monthly')
        same = periods.period_bounds('2026-09-29', 'Monthly')
        key = periods.claim_key('Acuerdo de soporte', *one)
        self.assertEqual(key, periods.claim_key('Acuerdo de soporte', *same))
        self.assertNotEqual(key, periods.claim_key('Acuerdo de diseño', *one))
        self.assertEqual(len(key), 64)

    def test_new_month_and_year_never_share_claim(self):
        keys = {periods.claim_key('Acuerdo', *periods.period_bounds(anchor, 'Monthly'))
                for anchor in ('2026-09-01', '2026-10-01', '2027-09-01')}
        self.assertEqual(len(keys), 3)

    def test_month_and_half_keys_differ(self):
        keys = {periods.claim_key('Acuerdo', *periods.period_bounds(anchor, frequency))
                for anchor, frequency in (('2026-09-01', 'Monthly'),
                    ('2026-09-01', 'Bimonthly'), ('2026-09-16', 'Bimonthly'))}
        self.assertEqual(len(keys), 3)
        # Different keys alone do not protect overlap: the SQL claim guard must
        # reject overlapping monthly/half-month claims across amendments.


if __name__ == '__main__':
    unittest.main()
