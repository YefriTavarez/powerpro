"""Rollback-only integration tests; run using scripts/test_employee_supplements_dev.py."""
import json
import os
import unittest
import uuid
from unittest.mock import patch

import frappe
from powerpro.supplements import service


@unittest.skipUnless(os.environ.get('POWERPRO_SUPPLEMENTS_DEV') == '1', 'Explicit Development runner required')
class EmployeeSupplementIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.point = 'employee_supplements_test'
        frappe.db.savepoint(self.point)
        self.addCleanup(self.cleanup)
        self.token = 'PP-SUP-' + uuid.uuid4().hex[:8]
        self.structure = frappe.copy_doc(frappe.get_doc('Salary Structure', 'General Quincenal'))
        self.structure.name = self.token
        self.structure.docstatus = 0
        self.structure.is_active = 'Yes'
        self.structure.salary_structure = self.token
        self.structure.insert().submit()
        self.company = self.structure.company
        frappe.get_doc(dict(doctype='Fiscal Year',year=self.token+'-FY',year_start_date='2099-01-01',
            year_end_date='2099-12-31',companies=[dict(company=self.company)])).insert()
        frappe.cache().delete_value('fiscal_years')
        self.config = frappe.get_single(service.SETTINGS)
        self.config.enabled = 0
        self.config.save()
        self.components = []
        for i,field in enumerate(service.rules.FIELDS):
            component = frappe.get_doc(dict(doctype='Salary Component', salary_component=self.token+'-'+str(i),
                salary_component_abbr='S'+uuid.uuid4().hex[:5],type='Earning',
                depends_on_payment_days=0, is_tax_applicable=0)).insert()
            self.components.append(component.name)
        self.holiday = frappe.get_doc(dict(doctype='Holiday List',holiday_list_name=self.token,
            from_date='2099-01-01',to_date='2099-12-31')).insert()
        self.employee = frappe.get_doc(dict(doctype='Employee',first_name=self.token,
            employee_number=str(uuid.uuid4().int)[:10],gender='Male',date_of_birth='1990-01-01',
            date_of_joining='2099-01-01',company=self.company,status='Active',holiday_list=self.holiday.name,
            naming_series='HR-EMP-',salary_currency='DOP',incentivo_especial=19720,asignacion_transporte=3800)).insert()
        self.payable=frappe.db.get_value('Account',{'company':self.company,'is_group':0,'account_type':''},'name')
        self.assignment = frappe.get_doc(dict(doctype='Salary Structure Assignment',employee=self.employee.name,
            salary_structure=self.structure.name,from_date='2099-01-01',base=75000,company=self.company,currency='DOP',payroll_payable_account=self.payable)).insert().submit()
        self.config.company=self.company
        self.config.currency='DOP'
        self.config.effective_from='2099-01-01'
        self.config.second_quincena_day='16'
        self.config.amount_precision='2'
        self.config.set('mappings',[])
        self.config.set('existing_salaries',[])
        for field,component in zip(service.rules.FIELDS,self.components):
            self.config.append('mappings',dict(source_field=field,salary_component=component))
        self.config.save()

    def cleanup(self):
        frappe.db.rollback(save_point=self.point)
        frappe.clear_cache(doctype=service.SETTINGS)
        frappe.clear_cache(doctype='DGII Payroll Settings')
        frappe.cache().delete_value('fiscal_years')

    def enable(self):
        self.config.enabled=1
        self.config.save()

    def entry(self,start='2099-01-01',end='2099-01-15',frequency='Bimonthly'):
        # Normal document lifecycle, except on_submit's auto-generation is deferred until the test invokes it.
        payable=self.payable
        doc=frappe.get_doc(dict(doctype='Payroll Entry',company=self.company,currency='DOP',exchange_rate=1,
            payroll_frequency=frequency,start_date=start,end_date=end,posting_date=end,
            payroll_payable_account=payable,cost_center=frappe.db.get_value('Company',self.company,'cost_center'),
            employees=[dict(employee=self.employee.name)],salary_slip_based_on_timesheet=0))
        doc.insert()
        with patch.object(type(doc),'on_submit',lambda self:None):doc.submit()
        return doc

    def slip(self,entry):
        return frappe.get_doc(dict(doctype='Salary Slip',employee=self.employee.name,company=self.company,
            currency='DOP',exchange_rate=1,salary_structure=self.structure.name,payroll_entry=entry.name,
            payroll_frequency=entry.payroll_frequency,start_date=entry.start_date,end_date=entry.end_date,
            posting_date=entry.end_date,salary_slip_based_on_timesheet=0)).insert()

    def legacy(self,amount=9860,recurring=True):
        data=dict(doctype='Additional Salary',employee=self.employee.name,company=self.company,currency='DOP',
            salary_component=self.components[0],amount=amount,is_recurring=int(recurring),overwrite_salary_structure_amount=0)
        data.update(dict(from_date='2099-01-01',to_date='2099-12-31') if recurring else dict(payroll_date='2099-01-15'))
        return frappe.get_doc(data).insert().submit()

    def associate(self,salary,treatment='Coverage'):
        self.config.append('existing_salaries',dict(additional_salary=salary.name,treatment=treatment,
                                                  source_field='incentivo_especial' if treatment=='Coverage' else None))

    def automatic(self):
        return frappe.get_all('Additional Salary',filters={'employee':self.employee.name,'pp_supplement_key':['is','set']},
                              fields=['name','amount','docstatus','salary_component','pp_supplement_field'])

    def test_disabled_does_not_generate(self):
        slip=self.slip(self.entry())
        self.assertFalse(slip.get(service.SNAPSHOT))
        self.assertEqual(self.automatic(),[])

    def test_new_slip_creates_full_halves_and_recalculation_reuses(self):
        self.enable()
        entry=self.entry()
        slip=self.slip(entry)
        self.assertEqual(sorted(r.amount for r in self.automatic()),[1900,9860])
        self.assertTrue(all(r.docstatus==1 for r in self.automatic()))
        slip.save()
        self.assertEqual(len(self.automatic()),2)
        snap=json.loads(slip.get(service.SNAPSHOT))
        self.assertEqual(len(snap['rows']),4)
        self.assertEqual(frappe.db.count(service.REVISION,{'employee':self.employee.name}),1)

    def test_submission_preserves_snapshot_and_complete_amount(self):
        self.enable();slip=self.slip(self.entry());raw=slip.get(service.SNAPSHOT)
        slip.submit()
        self.assertEqual(slip.get(service.SNAPSHOT),raw)
        self.assertEqual(len(self.automatic()),2)

    def test_recurring_coverage_is_reused_not_copied(self):
        salary=self.legacy();self.associate(salary);self.enable()
        slip=self.slip(self.entry())
        self.assertEqual(len(self.automatic()),1)
        self.assertEqual(json.loads(slip.get(service.SNAPSHOT))['rows'][0]['additional_salary'],salary.name)
        self.assertEqual(frappe.get_doc('Additional Salary',salary.name).amount,9860)

    def test_independent_orc_coexists_with_fixed_amount(self):
        salary=self.legacy(200);self.associate(salary,'Independent');self.enable()
        slip=self.slip(self.entry())
        earnings=[r.amount for r in slip.earnings if r.salary_component==self.components[0]]
        self.assertEqual(sum(earnings),10060)
        self.assertEqual(len(self.automatic()),2)

    def test_unclassified_existing_blocks_activation(self):
        self.legacy()
        with self.assertRaises(frappe.ValidationError):self.enable()
        self.assertEqual(self.automatic(),[])

    def test_mismatched_coverage_blocks_without_generating(self):
        salary=self.legacy(7000);self.associate(salary);self.enable()
        with self.assertRaises(frappe.ValidationError):self.slip(self.entry())
        self.assertEqual(self.automatic(),[])

    def test_new_manual_payment_must_be_explicitly_independent(self):
        self.enable()
        with self.assertRaises(frappe.ValidationError):self.legacy(200)
        salary=frappe.get_doc(dict(doctype='Additional Salary',employee=self.employee.name,company=self.company,
            currency='DOP',salary_component=self.components[0],amount=200,payroll_date='2099-01-15',
            pp_supplement_treatment='Independent')).insert().submit()
        self.assertEqual(salary.docstatus,1)

    def test_revision_closes_legacy_future_only_and_preserves_old_period(self):
        salary=self.legacy();self.associate(salary);self.enable()
        old=self.slip(self.entry())
        self.employee.reload();self.employee.incentivo_especial=30000
        self.employee.pp_supplements_effective_from='2099-02-01';self.employee.save()
        self.assertEqual(str(frappe.get_doc('Additional Salary',salary.name).to_date),'2099-01-31')
        old.reload().save()
        future=self.slip(self.entry('2099-02-01','2099-02-15'))
        row=json.loads(future.get(service.SNAPSHOT))['rows'][0]
        self.assertEqual(row['amount'],'15000.00')
        self.assertNotEqual(row['additional_salary'],salary.name)
        revision=frappe.get_doc(service.REVISION,row and json.loads(future.get(service.SNAPSHOT))['revision'])
        self.assertEqual(json.loads(revision.legacy_changes)[0]['old_to_date'],'2099-12-31')

    def test_prepared_period_blocks_retroactive_change(self):
        self.enable();self.slip(self.entry())
        self.employee.reload();self.employee.incentivo_especial=30000
        self.employee.pp_supplements_effective_from='2099-01-01'
        with self.assertRaises(frappe.ValidationError):self.employee.save()

    def test_repeated_employee_save_does_not_repeat_revision(self):
        self.enable();self.employee.reload();self.employee.incentivo_especial=30000
        self.employee.pp_supplements_effective_from='2099-02-01';self.employee.save()
        self.employee.save()
        self.assertEqual(frappe.db.count(service.REVISION,{'employee':self.employee.name}),2)

    def test_snapshot_and_generated_salary_cannot_be_forged(self):
        self.enable();slip=self.slip(self.entry());slip.set(service.SNAPSHOT,'{}')
        with self.assertRaises(frappe.ValidationError):slip.save()
        salary=frappe.get_doc('Additional Salary',self.automatic()[0].name)
        with self.assertRaises(frappe.ValidationError):salary.cancel()

    def test_changed_source_does_not_reinterpret_existing_draft(self):
        self.enable();slip=self.slip(self.entry())
        self.employee.reload();self.employee.incentivo_especial=30000
        self.employee.pp_supplements_effective_from='2099-02-01';self.employee.save()
        slip.reload().save()
        self.assertEqual(json.loads(slip.get(service.SNAPSHOT))['rows'][0]['amount'],'9860.00')

    def test_monthly_uses_full_amount(self):
        monthly=frappe.copy_doc(self.structure);monthly.docstatus=0;monthly.name=self.token+'-M'
        monthly.salary_structure=monthly.name;monthly.payroll_frequency='Monthly';monthly.insert().submit()
        frappe.get_doc(dict(doctype='Salary Structure Assignment',employee=self.employee.name,
            salary_structure=monthly.name,from_date='2099-02-01',base=75000,company=self.company,currency='DOP',payroll_payable_account=self.payable)).insert().submit()
        self.structure=monthly;self.enable()
        slip=self.slip(self.entry('2099-02-01','2099-02-28','Monthly'))
        self.assertEqual(sorted(r.amount for r in self.automatic()),[3800,19720])

    def test_zero_does_not_generate(self):
        self.employee.incentivo_especial=0;self.employee.asignacion_transporte=0;self.employee.save()
        self.enable();slip=self.slip(self.entry())
        self.assertEqual(self.automatic(),[])
        self.assertTrue(slip.get(service.SNAPSHOT))

    def test_configuration_cannot_reinterpret_history(self):
        self.enable();self.config.second_quincena_day='15'
        with self.assertRaises(frappe.ValidationError):self.config.save()

    def test_preview_does_not_generate(self):
        self.enable();entry=self.entry()
        slip=frappe.get_doc(dict(doctype='Salary Slip',employee=self.employee.name,company=self.company,
            currency='DOP',exchange_rate=1,salary_structure=self.structure.name,payroll_entry=entry.name,
            payroll_frequency=entry.payroll_frequency,start_date=entry.start_date,end_date=entry.end_date))
        slip.get_emp_and_working_day_details()
        self.assertEqual(self.automatic(),[])

    def test_inactive_employee_never_generates(self):
        self.enable();entry=self.entry()
        self.employee.reload();self.employee.status='Inactive';self.employee.save()
        with self.assertRaises(frappe.ValidationError):self.slip(entry)
        self.assertEqual(self.automatic(),[])

    def test_cancelling_payroll_and_regenerating_reuses_fixed_entitlement(self):
        self.enable();entry=self.entry();slip=self.slip(entry)
        names={r.name for r in self.automatic()}
        with patch.object(frappe,'enqueue',return_value=None) as queued:
            entry.reload().cancel()
            self.assertTrue(all(c.args[0]=='frappe.model.delete_doc.delete_dynamic_links' for c in queued.call_args_list))
        self.assertFalse(frappe.db.exists('Salary Slip',slip.name))
        self.assertEqual({r.name for r in self.automatic()},names)
        replacement=self.slip(self.entry())
        self.assertEqual({r.name for r in self.automatic()},names)
        self.assertTrue(replacement.get(service.SNAPSHOT))

    def test_paid_days_do_not_prorate_fixed_supplements(self):
        self.enable();slip=self.slip(self.entry())
        slip.leave_without_pay=5;slip.save()
        self.assertLess(slip.payment_days,slip.total_working_days)
        self.assertEqual(sorted(r.amount for r in slip.earnings if r.additional_salary),[1900,9860])

    def test_disabled_feature_keeps_history_for_enrolled_employees(self):
        self.enable();slip=self.slip(self.entry());self.config.enabled=0;self.config.save()
        self.employee.reload();self.employee.incentivo_especial=30000
        self.employee.pp_supplements_effective_from='2099-02-01';self.employee.save()
        slip.reload().save()
        self.assertEqual(frappe.db.count(service.REVISION,{'employee':self.employee.name}),2)

    def test_regular_worker_retries_and_stale_queue_arguments(self):
        from powerpro.supplements.worker import generate
        self.enable();entry=self.entry()
        args={k:entry.get(k) for k in ('salary_slip_based_on_timesheet','payroll_frequency','start_date','end_date',
            'company','posting_date','deduct_tax_for_unclaimed_employee_benefits',
            'deduct_tax_for_unsubmitted_tax_exemption_proof','exchange_rate','currency')}
        args['payroll_entry']=entry.name
        generate(entry,[self.employee.name],args)
        generate(entry,[self.employee.name],args)
        self.assertEqual(frappe.db.count('Salary Slip',{'payroll_entry':entry.name}),1)
        self.assertEqual(len(self.automatic()),2)
        with self.assertRaises(frappe.ValidationError):
            generate(entry,[self.employee.name],dict(args,currency='USD'))
        with self.assertRaises(frappe.ValidationError):generate(entry,[],args)

    def test_mixed_payroll_uses_full_month_for_monthly_employee(self):
        monthly=frappe.copy_doc(self.structure);monthly.docstatus=0;monthly.name=self.token+'-M'
        monthly.salary_structure=monthly.name;monthly.payroll_frequency='Monthly';monthly.insert().submit()
        frappe.get_doc(dict(doctype='Salary Structure Assignment',employee=self.employee.name,
            salary_structure=monthly.name,from_date='2099-02-01',base=75000,company=self.company,currency='DOP',
            payroll_payable_account=self.payable)).insert().submit()
        self.structure=monthly
        settings=frappe.get_single('DGII Payroll Settings');settings.include_monthly_in_second_quincena=1;settings.save()
        self.enable();entry=self.entry('2099-02-16','2099-02-28')
        slip=self.slip(entry)
        self.assertEqual(str(slip.start_date),'2099-02-01')
        self.assertEqual(slip.payroll_frequency,'Monthly')
        self.assertEqual(sorted(r.amount for r in self.automatic()),[3800,19720])

    def test_rolls_back_generated_additionals_when_slip_fails(self):
        self.enable();entry=self.entry();frappe.db.savepoint('before_bad_slip')
        from powerpro.controllers.salary_slip.salary_slip import SalarySlip
        with patch.object(SalarySlip,'validate',side_effect=frappe.ValidationError('forced downstream failure')):
            with self.assertRaises(frappe.ValidationError):self.slip(entry)
        self.assertEqual(len(self.automatic()),2)  # staged in the same transaction, not committed
        frappe.db.rollback(save_point='before_bad_slip')
        self.assertEqual(self.automatic(),[])
        self.assertEqual(frappe.db.count('Salary Slip',{'payroll_entry':entry.name}),0)

    def test_overlapping_second_payroll_cannot_duplicate(self):
        self.enable();entry=self.entry();self.slip(entry)
        with self.assertRaises(frappe.ValidationError):self.entry()
        self.assertEqual(len(self.automatic()),2)

    def test_missing_end_date_is_resolved_from_payroll_before_generation(self):
        self.enable();entry=self.entry()
        slip=frappe.get_doc(dict(doctype='Salary Slip',employee=self.employee.name,company=self.company,
            currency='DOP',exchange_rate=1,salary_structure=self.structure.name,payroll_entry=entry.name,
            payroll_frequency=entry.payroll_frequency,start_date=entry.start_date,posting_date=entry.end_date)).insert()
        self.assertEqual(str(slip.end_date),'2099-01-15')
        self.assertEqual(len(self.automatic()),2)

    def test_queue_dispatch_is_after_commit(self):
        from powerpro.supplements.worker import create_slips
        self.enable();entry=self.entry()
        with patch.dict(frappe.flags,{'enqueue_payroll_entry':True}), patch.object(frappe,'enqueue') as queued:
            entry.create_salary_slips()
        self.assertIs(queued.call_args.args[0],create_slips)
        self.assertTrue(queued.call_args.kwargs['enqueue_after_commit'])
        self.assertEqual(self.automatic(),[])

    def test_other_sites_without_snapshot_schema_keep_existing_payroll(self):
        from types import SimpleNamespace
        with patch.object(frappe,'get_meta',return_value=SimpleNamespace(has_field=lambda f:False)), \
             patch.object(frappe.db,'get_value',side_effect=AssertionError('Do not query absent columns')):
            service.validate_slip(SimpleNamespace())

    def test_untracked_employee_write_cannot_silently_change_entitlement(self):
        self.enable()
        frappe.db.set_value('Employee',self.employee.name,'incentivo_especial',12345)
        with self.assertRaises(frappe.ValidationError):self.slip(self.entry())
        self.assertEqual(self.automatic(),[])
