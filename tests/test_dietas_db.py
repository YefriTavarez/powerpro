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
        self.suffix = uuid.uuid4().hex[:10]
        self.company = frappe.db.get_value('Company', '_Test Company', 'name')
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
        if not frappe.db.exists('Mode of Payment', 'Cash'):
            frappe.get_doc(dict(doctype='Mode of Payment',mode_of_payment='Cash',type='Cash')).insert(ignore_permissions=True)
        self.raw('Dieta Payment Method','DIETA-METHOD-'+self.suffix,parent='IGC Settings',
            parenttype='IGC Settings',parentfield='dieta_payment_methods',company=self.company,mode_of_payment='Cash')

    def raw(self, dt, name, **values):
        doc=frappe.get_doc(dict(doctype=dt,name=name,**values));doc.db_insert();return doc

    def tearDown(self):
        frappe.db.rollback(save_point=self.point)
        frappe.set_user(self.original_user)

    def payload(self):
        context=service.work_call_context(self.call_name,self.date)
        row=context['rows'][0]
        args=dict(work_call=self.call_name,work_date=self.date,
            rows=[dict(employee=self.employee,amount=row['amount'],version=row['version'],reason='')],
            payment_date=self.date,mode_of_payment='Cash')
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

    def test_unique_daily_key_and_read_only_controller(self):
        service.confirm_payout(**self.payload());req=service._request(self.company,self.employee,self.date)
        req.amount=999
        with self.assertRaises(frappe.PermissionError):req.save(ignore_permissions=True)
        duplicate=frappe.get_doc(req.as_dict());duplicate.name='DIETA-DUP-'+self.suffix
        with self.assertRaises((frappe.UniqueValidationError,frappe.DuplicateEntryError)):
            duplicate.db_insert()

if __name__=='__main__':unittest.main()
