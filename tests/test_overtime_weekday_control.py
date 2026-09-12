"""Regression cases for optional weekday metadata on mixed-version sites."""
import unittest
from test_overtime_calendar import legacy

is_scheduled_workday = legacy.is_scheduled_workday
classify_workday = legacy.classify_workday


class WeekdayControl(unittest.TestCase):
    def test_native_calendar_without_custom_fields(self):
        self.assertFalse(is_scheduled_workday({}, 'custom_trabaja_sabado', calendar_weekly_off=True))
        self.assertTrue(is_scheduled_workday({}, 'custom_trabaja_lunes', calendar_weekly_off=False))

    def test_new_disabled_fields_preserve_calendar_both_ways(self):
        for control in (None, 0, '0'):
            shift = {'custom_control_dias_laborables': control, 'custom_trabaja_lunes': 0, 'custom_trabaja_sabado': 1}
            self.assertTrue(is_scheduled_workday(shift, 'custom_trabaja_lunes', calendar_weekly_off=False))
            self.assertFalse(is_scheduled_workday(shift, 'custom_trabaja_sabado', calendar_weekly_off=True))

    def test_enabled_weekday_override_recognizes_holiday_on_rest(self):
        shift = {'custom_control_dias_laborables': 1, 'custom_trabaja_domingo': 0}
        worked = is_scheduled_workday(shift, 'custom_trabaja_domingo', calendar_weekly_off=False)
        self.assertEqual(classify_workday(is_shift_workday=worked, has_legal_holiday=True), 'Legal Holiday on Weekly Rest')

    def test_enabled_workday_can_override_calendar_rest(self):
        self.assertTrue(is_scheduled_workday({'custom_control_dias_laborables': '1', 'custom_trabaja_sabado': '1'},
                                            'custom_trabaja_sabado', calendar_weekly_off=True))

    def test_legacy_weekday_override_remains_supported(self):
        self.assertFalse(is_scheduled_workday({'custom_trabaja_domingo': 0}, 'custom_trabaja_domingo', calendar_weekly_off=False))
        self.assertTrue(is_scheduled_workday({'custom_trabaja_domingo': 1}, 'custom_trabaja_domingo', calendar_weekly_off=True))

    def test_missing_weekday_still_uses_calendar(self):
        self.assertFalse(is_scheduled_workday({'custom_control_dias_laborables': 1}, 'custom_trabaja_domingo', calendar_weekly_off=True))


if __name__ == '__main__': unittest.main()
