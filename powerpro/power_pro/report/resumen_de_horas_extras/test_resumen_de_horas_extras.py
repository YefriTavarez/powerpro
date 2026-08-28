# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

import json
import unittest

from powerpro.power_pro.report.resumen_de_horas_extras.resumen_de_horas_extras import (
    summarize_adjustments,
)


class TestResumenDeHorasExtras(unittest.TestCase):
    def test_aggregates_payable_hours_without_double_counting_night_hours(self):
        breakdown = {
            "salary_structure_assignment": "SSA-0001",
            "currency": "DOP",
            "hourly_rate": 144.20,
            "total_amount": 4434.04,
            "lines": [
                {"component": "Horas Extras 35%", "amount": 973.33},
                {"component": "Horas Extras 100%", "amount": 3460.71},
                {"component": "Horas Nocturnas", "amount": 0},
            ],
        }
        rows = [
            {
                "name": "OT-ADJ-2026-00001",
                "employee": "HR-EMP-0001",
                "employee_name": "JULIO BAEZ DE JESÚS",
                "work_date": "2026-08-15",
                "regular_35_hours": 5,
                "regular_100_hours": 0,
                "holiday_100_hours": 12,
                "night_hours": 4,
                "settlement_hourly_rate": 144.20,
                "settlement_amount": 4434.04,
                "settlement_currency": "DOP",
                "settlement_breakdown": json.dumps(breakdown),
            }
        ]

        result = summarize_adjustments(rows, {"SSA-0001": 27489.60})

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["dates"], "15/08")
        self.assertEqual(result[0]["hours_35"], 5)
        self.assertEqual(result[0]["hours_100"], 12)
        self.assertEqual(result[0]["night_hours"], 4)
        self.assertEqual(result[0]["total_hours"], 17)
        self.assertEqual(result[0]["salary"], 27489.60)
        self.assertEqual(result[0]["amount_35"], 973.33)
        self.assertEqual(result[0]["amount_100"], 3460.71)
        self.assertEqual(result[0]["total_amount"], 4434.04)

    def test_groups_dates_and_combines_regular_and_holiday_100_percent_hours(self):
        def row(work_date, regular_100, holiday_100, amount):
            return {
                "employee": "HR-EMP-0002",
                "employee_name": "EMPLOYEE TWO",
                "work_date": work_date,
                "regular_35_hours": 1,
                "regular_100_hours": regular_100,
                "holiday_100_hours": holiday_100,
                "night_hours": 0,
                "settlement_hourly_rate": 100,
                "settlement_amount": amount,
                "settlement_currency": "DOP",
                "settlement_breakdown": {
                    "salary_structure_assignment": "SSA-0002",
                    "lines": [],
                },
            }

        result = summarize_adjustments(
            [row("2026-08-16", 2, 0, 535), row("2026-08-15", 0, 3, 735)],
            {"SSA-0002": 19064},
        )

        self.assertEqual(result[0]["dates"], "15/08, 16/08")
        self.assertEqual(result[0]["hours_35"], 2)
        self.assertEqual(result[0]["hours_100"], 5)
        self.assertEqual(result[0]["total_hours"], 7)
        self.assertEqual(result[0]["total_amount"], 1270)


if __name__ == "__main__":
    unittest.main()
