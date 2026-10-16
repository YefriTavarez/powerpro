from datetime import date, datetime
from decimal import Decimal
from unittest import TestCase
from powerpro.payroll_rules.additional_salary_schedule import allocation, money, as_date, SPLIT, FIRST, SECOND


class AllocationTest(TestCase):
    def test_three_modes(self):
        for mode, expected in ((SPLIT,(500,500)),(FIRST,(1000,0)),(SECOND,(0,1000))):
            with self.subTest(mode=mode):
                self.assertEqual(allocation(1000,mode,'2026-10-01','2026-10-15','Bimonthly'),expected[0])
                self.assertEqual(allocation(1000,mode,'2026-10-16','2026-10-31','Bimonthly'),expected[1])

    def test_month_end_28_29_30_31(self):
        for year,month,last in ((2026,2,28),(2028,2,29),(2026,9,30),(2026,10,31)):
            with self.subTest(year=year,month=month):
                self.assertEqual(allocation(90,SECOND,date(year,month,16),date(year,month,last),'Bimonthly'),90)

    def test_rounding_conserves_month(self):
        for value in ('0.01','1.01','1000.01','1000.03','123456.79'):
            first=allocation(value,SPLIT,'2026-10-01','2026-10-15','Bimonthly')
            second=allocation(value,SPLIT,'2026-10-16','2026-10-31','Bimonthly')
            self.assertEqual(first+second,Decimal(value))
        self.assertEqual(allocation('1.01',SPLIT,'2026-10-01','2026-10-15','Bimonthly'),Decimal('0.51'))

    def test_custom_precision_and_calendar(self):
        self.assertEqual(allocation('1.001',SPLIT,'2026-10-01','2026-10-14','Bimonthly',precision=3,second_day=15),Decimal('0.501'))
        self.assertEqual(allocation('1.001',SPLIT,'2026-10-15','2026-10-31','Bimonthly',precision=3,second_day=15),Decimal('0.500'))

    def test_monthly_once_for_all_modes(self):
        for mode in (SPLIT,FIRST,SECOND):
            self.assertEqual(allocation(80,mode,'2026-10-01','2026-10-31','Monthly'),80)

    def test_reject_partial_cross_month_and_other_frequency(self):
        for start,end,freq in (('2026-10-02','2026-10-15','Bimonthly'),('2026-10-16','2026-10-30','Bimonthly'),('2026-10-16','2026-11-15','Bimonthly'),('2026-10-01','2026-10-31','Weekly'),('2026-10-16','2026-10-31','Monthly')):
            with self.subTest(period=(start,end,freq)), self.assertRaises(ValueError):
                allocation(5,SECOND,start,end,freq)

    def test_invalid_mode_calendar_amount(self):
        for value in (-1,'NaN','Infinity','abc'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                allocation(value,SECOND,'2026-10-01','2026-10-31','Monthly')
        for day in (0,1,29,40):
            with self.assertRaises(ValueError):
                allocation(2,SECOND,'2026-10-01','2026-10-31','Monthly',second_day=day)
        with self.assertRaises(ValueError):
            allocation(2,'unknown','2026-10-01','2026-10-31','Monthly')
        with self.assertRaises(ValueError):
            money(2,9)

    def test_date_normalization(self):
        self.assertEqual(as_date(datetime(2026,10,1,14)), date(2026,10,1))
