# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import unittest
from powerpro.controllers.project.utils import get_duration_in_minutes


class TestGetDurationInMinutes(unittest.TestCase):
    def test_minutes(self):
        self.assertEqual(get_duration_in_minutes(45, "in Minutes"), 45)
        self.assertEqual(get_duration_in_minutes(0, "in Minutes"), 30)  # default
        self.assertEqual(get_duration_in_minutes(None, "in Minutes"), 30)  # default

    def test_hours(self):
        self.assertEqual(get_duration_in_minutes(2, "in Hours"), 120)
        self.assertEqual(get_duration_in_minutes(0, "in Hours"), 30)  # default
        self.assertEqual(get_duration_in_minutes(None, "in Hours"), 30)  # default

    def test_days(self):
        self.assertEqual(get_duration_in_minutes(1, "in Days"), 1440)
        self.assertEqual(get_duration_in_minutes(0, "in Days"), 30)  # default
        self.assertEqual(get_duration_in_minutes(None, "in Days"), 30)  # default

    def test_default_args(self):
        self.assertEqual(get_duration_in_minutes(), 30)

    def test_invalid_measurement(self):
        # Should default to minutes if measurement is not recognized
        # self.assertRaises(ValueError, "Invalid measurement unit: invalid. Must be one of 'in Minutes', 'in Hours', or 'in Days'.")
        with self.assertRaises(ValueError):
            get_duration_in_minutes(10, "invalid")

if __name__ == "__main__":
    unittest.main()
