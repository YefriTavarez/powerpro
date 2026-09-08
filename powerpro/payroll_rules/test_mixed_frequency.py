from datetime import date
from unittest import TestCase

from .mixed_frequency import is_second_quincena, periods_overlap, salary_period


class MixedFrequencyPeriodTest(TestCase):
    def test_only_month_closing_bimonthly_entries(self):
        cases = [
            ("Bimonthly", "2026-08-16", "2026-08-31", False, True),
            ("Bimonthly", "2026-08-15", "2026-08-31", False, True),
            ("Bimonthly", "2026-08-01", "2026-08-15", False, False),
            ("Monthly", "2026-08-01", "2026-08-31", False, False),
            ("Bimonthly", "2026-08-16", "2026-08-31", True, False),
            ("Bimonthly", "2026-08-16", "2026-09-30", False, False),
            ("Bimonthly", "2026-08-16", "2026-08-30", False, False),
            ("Bimonthly", "2026-08-20", "2026-08-31", False, False),
            ("Bimonthly", None, None, False, False),
        ]
        for frequency, start, end, timesheet, expected in cases:
            with self.subTest(start=start, end=end, frequency=frequency, timesheet=timesheet):
                self.assertEqual(is_second_quincena(frequency, start, end, timesheet), expected)

    def test_month_lengths_and_leap_year(self):
        for end in ("2026-02-28", "2028-02-29", "2026-04-30", "2026-12-31"):
            self.assertTrue(is_second_quincena("Bimonthly", end[:8] + "16", end))
            period = salary_period("Monthly", end[:8] + "16", end)
            self.assertEqual(period["start_date"], date.fromisoformat(end[:8] + "01"))
            self.assertEqual(period["end_date"], date.fromisoformat(end))

    def test_bimonthly_dates_are_preserved(self):
        period = salary_period("Bimonthly", "2026-08-16", "2026-08-31")
        self.assertEqual(period["start_date"], date(2026, 8, 16))

    def test_full_month_conflicts_with_either_half_but_adjacent_halves_do_not(self):
        self.assertTrue(periods_overlap("2026-08-01", "2026-08-31", "2026-08-01", "2026-08-15"))
        self.assertTrue(periods_overlap("2026-08-01", "2026-08-31", "2026-08-16", "2026-08-31"))
        self.assertFalse(periods_overlap("2026-08-16", "2026-08-31", "2026-08-01", "2026-08-15"))
