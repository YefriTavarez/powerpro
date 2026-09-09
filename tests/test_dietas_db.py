"""Opt-in development DB tests. Never run this module on production.

Run from an initialized development Frappe console/test runner, with the source
checkout installed and POWERPRO_DIETA_DEV_TESTS=1. Fixtures live in a rollback-only
transaction; this does not certify cross-session concurrency or GL posting.
"""
import os
import unittest
import uuid
from datetime import timedelta
from unittest.mock import patch

ENABLED = os.environ.get('POWERPRO_DIETA_DEV_TESTS') == '1'
if ENABLED:
    import frappe
    from frappe.utils import getdate
    from powerpro.dietas import service, accounting


@unittest.skipUnless(ENABLED, 'Requires an explicitly authorized isolated development site')
class DietaDatabaseTest(unittest.TestCase):
    def setUp(self):
        self.original_user = frappe.session.user
        frappe.set_user('Administrator')
        self.point = 'dieta_test_' + uuid.uuid4().hex
        frappe.db.savepoint(self.point)
        self.addCleanup(self.cleanup_transaction)
        self.suffix = uuid.uuid4().hex[:10]
        self.company = frappe.db.get_value('Company', os.environ.get('POWERPRO_DIETA_TEST_COMPANY', '_Test Company'), 'name')
        if not self.company:
            self.skipTest('Create the standard _Test Company development fixture first')
        self.date = str(getdate())
        self.call_name = 'DIETA-TEST-' + self.suffix
        self.employee = 'DIETA-EMP-' + self.suffix
        # Raw inserts are isolated fixture construction only. API operations below
        # use real controllers, metadata, permissions, SQL and savepoints.
        self.raw('Employee', self.employee, employee_name='Dieta Test', first_name='Dieta',
                 company=self.company, status='Active', department=None, user_id=None)
        call = self.raw('Overtime Work Call', self.call_name, docstatus=1,
            company=self.company, reason='Isolated dieta test', status='Authorized',
            from_date=self.date, to_date=self.date)
        row = call.append('dates', dict(work_date=self.date, start_time='20:00:00', end_time='04:00:00', allows_dieta=1))
        row.db_insert()
        row = call.append('employees', dict(employee=self.employee, employee_name='Dieta Test'))
        row.db_insert()
        self.auth_name = 'DIETA-AUTH-' + self.suffix
        self.raw('Overtime Authorization', self.auth_name, docstatus=1, employee=self.employee,
            employee_name='Dieta Test', company=self.company, work_date=self.date,
            overtime_work_call=self.call_name, authorization_start=self.date+' 20:00:00',
            authorization_end=str(getdate()+timedelta(days=1))+' 04:00:00')
        # Avoid duplicates with any developer's existing configuration, restored by rollback.
        frappe.db.delete('Dieta Company Settings', {'company':self.company})
        frappe.db.delete('Dieta Payment Method', {'company':self.company})
        self.raw('Dieta Company Settings','DIETA-CFG-'+self.suffix, parent='IGC Settings',
            parenttype='IGC Settings',parentfield='dieta_companies',company=self.company,enabled=1,default_amount=300,generate_journal_entry=0)
        self.payment_method = frappe.db.get_value('Mode of Payment', {'type':'Cash','enabled':1}, 'name')
        if not self.payment_method:
            self.skipTest('Configure an enabled Cash payment method in the development site first')
        self.raw('Dieta Payment Method','DIETA-METHOD-'+self.suffix,parent='IGC Settings',
            parenttype='IGC Settings',parentfield='dieta_payment_methods',company=self.company,mode_of_payment=self.payment_method)

    def raw(self, dt, name, **values):
        doc=frappe.get_doc(dict(doctype=dt,name=name,**values));doc.db_insert();return doc

    def cleanup_transaction(self):
        frappe.db.rollback(save_point=self.point)
        frappe.set_user(self.original_user)

    def payload(self):
        context=service.work_call_context(self.call_name,self.date)
        row=context['rows'][0]
        args=dict(work_call=self.call_name,work_date=self.date,
            rows=[dict(employee=self.employee,amount=row['amount'],version=row['version'],reason='')],
            payment_date=self.date,mode_of_payment=self.payment_method)
        preview=service.preview_payout(**args)
        return dict(**args,token=preview['token'],idempotency_key=str(uuid.uuid4()))

    def test_real_document_save_and_idempotent_retry(self):
        args=self.payload();first=service.confirm_payout(**args);second=service.confirm_payout(**args)
        self.assertEqual(first['batch'],second['batch'])
        req=service._request(self.company,self.employee,self.date)
        self.assertEqual(req.payment_status,'Paid')
        self.assertEqual(req.amount,300)
        with self.assertRaises(frappe.ValidationError):self.payload()

    def test_real_savepoint_restores_requests_on_failure(self):
        args=self.payload();original=service._save
        def fail_batch(doc,*a,**kw):
            if doc.doctype==service.BATCH:raise RuntimeError('Injected storage failure')
            return original(doc,*a,**kw)
        with patch.object(service,'_save',side_effect=fail_batch),self.assertRaises(RuntimeError):
            service.confirm_payout(**args)
        self.assertIsNone(service._request(self.company,self.employee,self.date))

    def enable_accounting(self):
        currency=frappe.db.get_value('Company',self.company,'default_currency')
        expense=frappe.db.get_value('Account',{'company':self.company,'is_group':0,'disabled':0,'root_type':'Expense','account_currency':currency},'name')
        cash=frappe.db.get_value('Account',{'company':self.company,'is_group':0,'disabled':0,'account_type':'Cash','account_currency':currency},'name')
        center=frappe.db.get_value('Cost Center',{'company':self.company,'is_group':0},'name')
        self.assertTrue(expense and cash and center,'Development accounting fixtures are required')
        frappe.db.set_value('Dieta Company Settings','DIETA-CFG-'+self.suffix,dict(generate_journal_entry=1,expense_account=expense,cost_center=center))
        frappe.db.set_value('Dieta Payment Method','DIETA-METHOD-'+self.suffix,'payment_account',cash)

    def test_real_draft_journal_and_repeat_generation(self):
        self.enable_accounting()
        before=frappe.db.count('GL Entry')
        result=service.confirm_payout(**self.payload())
        accounting.generate_journal(result['batch'])
        batch=frappe.get_doc(service.BATCH,result['batch'])
        self.assertEqual(batch.accounting_status,'Draft',batch.accounting_error)
        je=frappe.get_doc('Journal Entry',batch.journal_entry)
        self.assertEqual(je.docstatus,0)
        self.assertEqual(je.total_debit,300)
        self.assertEqual(je.total_credit,300)
        self.assertEqual(frappe.db.count('GL Entry'),before)
        accounting.generate_journal(batch.name)
        self.assertEqual(frappe.db.get_value(service.BATCH,batch.name,'journal_entry'),je.name)

    def test_real_accounting_failure_preserves_payout(self):
        self.enable_accounting()
        result=service.confirm_payout(**self.payload())
        with patch.object(accounting,'_validate_account',side_effect=ValueError('Injected account failure')):
            accounting.generate_journal(result['batch'])
        self.assertEqual(frappe.db.get_value(service.BATCH,result['batch'],'accounting_status'),'Error')
        self.assertEqual(service._request(self.company,self.employee,self.date).payment_status,'Paid')
        accounting.generate_journal(result['batch'])
        self.assertEqual(frappe.db.get_value(service.BATCH,result['batch'],'accounting_status'),'Draft')

    def test_real_source_cancellation_blocks_stale_preview(self):
        args=self.payload()
        auth=frappe.get_doc('Overtime Authorization',self.auth_name)
        auth.cancel()
        with self.assertRaises(frappe.ValidationError):service.confirm_payout(**args)
        self.assertIsNone(service._request(self.company,self.employee,self.date))

    def test_real_cancel_after_payment_preserves_history(self):
        result=service.confirm_payout(**self.payload())
        auth=frappe.get_doc('Overtime Authorization',self.auth_name)
        auth.cancel()
        req=service._request(self.company,self.employee,self.date)
        self.assertEqual(req.payment_status,'Paid')
        self.assertEqual(req.review_required,1)
        self.assertEqual(req.payout_batch,result['batch'])

    def test_real_employee_request_reused_by_manager(self):
        user='dieta-'+self.suffix+'@example.invalid'
        self.raw('User',user,email=user,first_name='Dieta Test',enabled=1,user_type='Website User')
        frappe.db.set_value('Employee',self.employee,'user_id',user)
        frappe.set_user(user)
        request=service.request_dieta(self.auth_name,'Meal for authorized work')
        self.assertEqual(len(service.my_dietas()['requests']),1)
        frappe.set_user('Administrator')
        service.confirm_payout(**self.payload())
        req=frappe.get_doc(service.REQUEST,request['request'])
        self.assertEqual(req.origin,'Employee')
        self.assertEqual(req.payment_status,'Paid')

    def test_unique_daily_key_and_read_only_controller(self):
        service.confirm_payout(**self.payload());req=service._request(self.company,self.employee,self.date)
        req.amount=999
        with self.assertRaises(frappe.PermissionError):req.save(ignore_permissions=True)
        duplicate=frappe.get_doc(req.as_dict());duplicate.name='DIETA-DUP-'+self.suffix
        with self.assertRaises((frappe.UniqueValidationError,frappe.DuplicateEntryError)):
            duplicate.db_insert()

if __name__=='__main__':unittest.main()
