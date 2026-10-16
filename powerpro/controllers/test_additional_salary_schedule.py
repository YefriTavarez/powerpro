"""Framework-boundary tests with mocked reads; no payroll or live data written."""
import json
import sys
from types import ModuleType
from unittest import TestCase
from unittest.mock import Mock, patch
import frappe
from powerpro.controllers import additional_salary_schedule as service
from powerpro.payroll_rules.additional_salary_schedule import FIRST, SECOND, SPLIT


def row(**values):
    return frappe._dict(values)

def fail(message, *args, **kwargs):
    raise ValueError(message)


class Slip(frappe._dict):
    def set(self,key,value):
        self[key]=value

    def update_component_row(self, component, amount, component_type, source, is_recurring=0):
        for existing in self[component_type]:
            if existing.additional_salary==source.name:
                existing.amount=amount
                return
        self[component_type].append(row(additional_salary=source.name,amount=amount,salary_component=source.component,
                                       is_recurring_additional_salary=is_recurring))


class RecurringControllerTest(TestCase):
    def setUp(self):
        self.record=row(name='AS-TEST', employee='TEST', company='TEST', currency='DOP', salary_component='Discount',
                        type='Deduction', amount=1000, is_recurring=1, from_date='2026-01-01',to_date='2027-12-31',
                        payroll_date=None,docstatus=1,disabled=0,overwrite_salary_structure_amount=0,
                        deduct_full_tax_on_selected_payroll_date=0,
                        **{service.MODE:SECOND,service.EFFECTIVE:'2026-10-01'})
        self.slip=Slip(employee='TEST',company='TEST',currency='DOP',start_date='2026-10-01',end_date='2026-10-15',
                       payroll_frequency='Bimonthly',salary_slip_based_on_timesheet=0,earnings=[],deductions=[])
        self.patches=[]
        self.mock('installed',return_value=True)
        self.mock('second_day',return_value=16)
        self.rows=self.start(patch.object(service.frappe,'get_all',return_value=[self.record]))
        self.start(patch.object(service.frappe,'get_precision',return_value=2))
        self.start(patch.object(service.frappe,'get_cached_value',return_value=True))
        self.start(patch.object(service.frappe,'throw',side_effect=fail))
        native=ModuleType('hrms.payroll.doctype.salary_slip.salary_slip')
        native.get_salary_component_data=lambda name:row(salary_component=name)
        self.start(patch.dict(sys.modules,{'hrms.payroll.doctype.salary_slip.salary_slip':native}))

    def start(self,context):
        value=context.start();self.addCleanup(context.stop);return value

    def mock(self,name,**kwargs):
        return self.start(patch.object(service,name,**kwargs))

    def second(self):
        self.slip.update(start_date='2026-10-16',end_date='2026-10-31')

    def test_second_only_idempotent_then_change_period_removes_row(self):
        self.assertTrue(service.add_components(self.slip,'deductions'))
        self.assertEqual(self.slip.deductions,[])
        self.second()
        for _ in range(3):
            self.assertTrue(service.add_components(self.slip,'deductions'))
            self.assertEqual(len(self.slip.deductions),1)
            self.assertEqual(self.slip.deductions[0].amount,1000)
        self.slip.update(start_date='2026-10-01',end_date='2026-10-15')
        service.add_components(self.slip,'deductions')
        self.assertEqual(self.slip.deductions,[])
        self.assertEqual(json.loads(self.slip[service.SNAPSHOT])['deductions']['rows'][0]['allocated_base'],0)
        self.assertEqual(self.record.amount,1000)

    def test_legacy_and_future_policy_native_fallback(self):
        self.record[service.MODE]=''
        self.assertFalse(service.add_components(self.slip,'deductions'))
        self.record[service.MODE]=SECOND
        self.record[service.EFFECTIVE]='2026-11-01'
        self.assertFalse(service.add_components(self.slip,'deductions'))

    def test_uninstalled_native_fallback(self):
        self.mock('installed',return_value=False)
        self.assertFalse(service.add_components(self.slip,'deductions'))
        self.rows.assert_not_called()

    def test_punctual_preserved_when_scheduled_source_excluded(self):
        punctual=self.record.copy();punctual.update(name='ONCE',is_recurring=0,payroll_date='2026-10-10',amount=70)
        punctual[service.MODE]='';punctual[service.EFFECTIVE]=None
        self.rows.return_value=[self.record,punctual]
        service.add_components(self.slip,'deductions')
        self.assertEqual([(x.additional_salary,x.amount) for x in self.slip.deductions],[('ONCE',70)])

    def test_cancelled_disabled_expired_cleanup(self):
        for field,value in (('disabled',1),('docstatus',2),('to_date','2026-09-30')):
            with self.subTest(field=field):
                old=self.record[field];self.record[field]=value
                self.slip.deductions=[row(additional_salary='AS-TEST',amount=1000)]
                service.add_components(self.slip,'deductions')
                self.assertEqual(self.slip.deductions,[])
                self.record[field]=old

    def test_expired_does_not_block_other_frequencies(self):
        self.record.to_date='2026-09-30'
        self.slip.salary_slip_based_on_timesheet=1
        self.slip.payroll_frequency='Weekly'
        self.assertFalse(service.add_components(self.slip,'deductions'))

    def test_mismatch_or_partial_period_fails_closed(self):
        self.second()
        for field,value in (('company','OTHER'),('currency','USD')):
            old=self.record[field];self.record[field]=value
            with self.assertRaises(ValueError):
                service.add_components(self.slip,'deductions')
            self.record[field]=old
        self.slip.end_date='2026-10-30'
        with self.assertRaises(ValueError):
            service.add_components(self.slip,'deductions')

    def test_missing_effective_date_rejected_not_full_legacy(self):
        self.record[service.EFFECTIVE]=None
        with self.assertRaises(ValueError):
            service.add_components(self.slip,'deductions')

    def test_monthly_full_amount_once(self):
        self.slip.update(payroll_frequency='Monthly',end_date='2026-10-31')
        for mode in (FIRST,SECOND,SPLIT):
            self.record[service.MODE]=mode
            service.add_components(self.slip,'deductions')
            self.assertEqual(len(self.slip.deductions),1)
            self.assertEqual(self.slip.deductions[0].amount,1000)

    def test_boundary_dates_and_earning_routing(self):
        self.record.type='Earning';self.record[service.MODE]=FIRST
        service.add_components(self.slip,'earnings')
        self.assertEqual(self.slip.earnings[0].amount,1000)
        self.assertEqual(self.rows.call_args.kwargs['filters']['type'],'Earning')

    def test_configuration_guard_before_any_save(self):
        doc=self.record.copy();doc[service.MODE]=SECOND
        doc.get_doc_before_save=lambda:None
        self.mock('lock_employee')
        db=Mock();db.exists.return_value=False
        self.start(patch.object(service.frappe,'db',db))
        self.rows.return_value=[row(name='POSTED')]
        with self.assertRaisesRegex(ValueError,'validada'):
            service.validate_schedule(doc)
        self.assertEqual(doc.amount,1000)

    def test_unchanged_configuration_does_not_touch_posted_payroll(self):
        doc=self.record.copy();old=self.record.copy()
        doc.get_doc_before_save=lambda:old
        lock=self.mock('lock_employee')
        db=Mock();db.exists.return_value=False
        self.start(patch.object(service.frappe,'db',db))
        service.validate_schedule(doc)
        lock.assert_not_called()

    def test_automatic_complement_is_protected(self):
        doc=self.record.copy();doc.pp_supplement_key='AUTO';doc.get_doc_before_save=lambda:None
        with self.assertRaisesRegex(ValueError,'automáticos'):
            service.validate_schedule(doc)
