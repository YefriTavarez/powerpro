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
    from powerpro.dietas import service, accounting, request_edit


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
            rows=[dict(employee=self.employee,amount=row['amount'],version=row['version'],cost_center=row.get('cost_center'),reason='')],
            payment_date=self.date,mode_of_payment=self.payment_method)
        preview=service.preview_payout(**args)
        return dict(**args,token=preview['token'],idempotency_key=str(uuid.uuid4()))

    def scoped_manager(self):
        """Rollback-only identity with real roles and a real User Permission."""
        user = 'dieta-scope-' + self.suffix + '@example.invalid'
        self.raw('User', user, email=user, first_name='Dieta Scope Test',
                 enabled=1, user_type='System User')
        self.raw('Has Role', 'DIETA-ROLE-' + self.suffix, parent=user,
                 parenttype='User', parentfield='roles', role='HR Manager')
        other = self.employee + '-OTHER'
        self.raw('Employee', other, employee_name='Other Dieta Test', first_name='Other',
                 company=self.company, status='Active', user_id=None)
        permission = self.raw('User Permission', 'DIETA-PERM-' + self.suffix,
                 user=user, allow='Employee', for_value=other, hide_descendants=1,
                 apply_to_all_doctypes=0, applicable_for='Leave Application')
        self.addCleanup(frappe.clear_cache, user=user)
        frappe.set_user(user)
        return user, permission

    def test_direct_request_respects_real_permission_applicability(self):
        user, permission = self.scoped_manager()
        currency = frappe.db.get_value('Company', self.company, 'default_currency')
        def draft():
            return frappe.get_doc(dict(doctype=service.REQUEST, employee=self.employee,
                company=self.company, work_date=self.date, amount=300, currency=currency))

        request = draft()
        request.insert()
        self.assertEqual((request.approval_status, request.payment_status), ('Pending', 'Unpaid'))
        self.assertEqual(request.initiated_by, user)
        request.check_permission('read')
        self.assertEqual(frappe.get_list(service.REQUEST, filters={'name': request.name},
                                        pluck='name'), [request.name])
        # The same Employee restriction must still apply globally or to Dietas.
        for applicable_for in ('', service.REQUEST):
            with self.subTest(applicable_for=applicable_for):
                frappe.db.set_value('User Permission', permission.name, {
                    'applicable_for': applicable_for,
                    'apply_to_all_doctypes': int(not applicable_for),
                })
                frappe.cache.hdel('user_permissions', user)
                self.assertFalse(frappe.has_permission(service.REQUEST, 'create', doc=draft()))
                self.assertFalse(frappe.has_permission(service.REQUEST, 'read', doc=request))
                self.assertEqual(frappe.get_list(service.REQUEST,
                    filters={'name': request.name}, pluck='name'), [])

    def test_real_batch_scope_blocks_stale_payout_before_writes(self):
        user, permission = self.scoped_manager()
        # Work Call read rights are independent; keep this test focused on the
        # real Dieta permission/service paths under a non-Administrator identity.
        with patch.object(service, '_call', return_value=frappe.get_doc('Overtime Work Call', self.call_name)):
            args = self.payload()
            frappe.db.set_value('User Permission', permission.name, 'applicable_for', service.BATCH)
            frappe.cache.hdel('user_permissions', user)
            with self.assertRaises(frappe.PermissionError):
                service.confirm_payout(**args)
        self.assertIsNone(service._request(self.company, self.employee, self.date))
        self.assertFalse(frappe.db.exists(service.BATCH, {'overtime_work_call': self.call_name}))

    def direct_request(self):
        return frappe.get_doc(dict(doctype=service.REQUEST, employee=self.employee,
            company=self.company, work_date=self.date, amount=300,
            currency=frappe.db.get_value('Company', self.company, 'default_currency'))).insert()

    def test_creator_can_edit_saved_request_with_real_hooks_and_server_scripts(self):
        user, permission = self.scoped_manager()
        # Use the production creator role, without HR Manager or payment privileges.
        frappe.db.set_value('Has Role', 'DIETA-ROLE-' + self.suffix, 'role', 'Gerente Finanzas')
        frappe.clear_cache(user=user)
        doc = self.direct_request()
        self.assertTrue(request_edit.get_context(doc.name)['can_edit'])
        doc.notes = 'Generic CRUD stays denied'
        with self.assertRaises(frappe.PermissionError):
            doc.save()
        doc.reload()
        before = doc.as_dict()
        request_edit.update_request(doc.name, str(doc.modified), 350, 'Corregir monto y notas')
        doc.reload()
        self.assertEqual((doc.amount, doc.notes), (350, 'Corregir monto y notas'))
        for field in ('employee','company','work_date','currency','day_key','default_amount','origin',
                      'initiated_by','approval_status','payment_status','approved_by','paid_by','payout_batch'):
            self.assertEqual(doc.get(field), before.get(field), field)
        self.assertEqual(frappe.parse_json(doc.audit_log)[-1]['user'], user)
        self.assertEqual(frappe.parse_json(doc.audit_log)[-1]['action'], 'edit')
        # Frappe filters unknown RPC arguments, but the narrow service never reads them.
        frappe.call('powerpro.dietas.request_edit.update_request', request=doc.name,
            modified=str(doc.modified), amount=350, notes='Solo notas', employee='forged',
            approval_status='Approved', payment_status='Paid', audit_log='[]')
        doc.reload()
        self.assertEqual((doc.employee, doc.approval_status, doc.payment_status),
                         (self.employee, 'Pending', 'Unpaid'))
        self.assertEqual(len(frappe.parse_json(doc.audit_log)), 3)
        for scope in ('', service.REQUEST):
            frappe.db.set_value('User Permission', permission.name, {
                'applicable_for':scope, 'apply_to_all_doctypes':int(not scope)})
            frappe.cache.hdel('user_permissions', user)
            with self.assertRaises(frappe.PermissionError):
                request_edit.update_request(doc.name, str(doc.modified), 300, 'Denied')

    def test_edit_rechecks_approval_payment_and_stale_versions(self):
        doc = self.direct_request()
        version = str(doc.modified)
        request_edit.update_request(doc.name, version, 300, 'First')
        with self.assertRaises(frappe.ValidationError):
            request_edit.update_request(doc.name, version, 300, 'Stale browser')
        doc.reload()
        for status in ('Approved', 'Rejected', 'Cancelled'):
            frappe.db.set_value(service.REQUEST, doc.name, 'approval_status', status)
            with self.assertRaises(frappe.PermissionError):
                request_edit.update_request(doc.name, str(doc.modified), 300, 'Denied')
        frappe.db.set_value(service.REQUEST, doc.name, {'approval_status':'Pending', 'payment_status':'Paid'})
        with self.assertRaises(frappe.PermissionError):
            request_edit.update_request(doc.name, str(doc.modified), 300, 'Denied')

    def test_custom_doctype_serves_versioned_edit_dialog(self):
        from powerpro.custom_hr import installer
        from frappe.desk.form.meta import get_meta
        desired, conflicts = installer._script_plan()
        self.assertEqual(conflicts, [])
        script = next(row for row in desired if row['name'] == 'PowerPro HR v1 - Solicitud de Dieta')
        current = frappe.get_doc('Client Script', script['name'])
        current.update(script)
        current.save(ignore_permissions=True)
        self.addCleanup(frappe.clear_cache, doctype=service.REQUEST)
        meta = get_meta(service.REQUEST, cached=False)
        self.assertEqual(meta.custom, 1)
        self.assertIn('powerpro.dietas.request_edit.', meta.get('__custom_js'))
        self.assertIn('frm.disable_save()', meta.get('__custom_js'))
        self.assertIn('Editar solicitud', meta.get('__custom_js'))

    def test_saved_direct_request_can_continue_through_existing_work_call_flow(self):
        doc = frappe.get_doc(dict(doctype=service.REQUEST, employee=self.employee,
            company=self.company, work_date=self.date, amount=300,
            overtime_work_call=self.call_name, authorization=self.auth_name,
            currency=frappe.db.get_value('Company', self.company, 'default_currency'))).insert()
        request_edit.update_request(doc.name, str(doc.modified), 350, 'Monto corregido')
        context = service.work_call_context(self.call_name, self.date)
        row = context['rows'][0]
        selection = [dict(employee=self.employee, version=row['version'], amount=row['amount'], reason='')]
        service.manage_requests(self.call_name, self.date, selection, 'approve')
        self.assertFalse(request_edit.get_context(doc.name)['can_edit'])
        result = service.confirm_payout(**self.payload())
        doc.reload()
        self.assertEqual((doc.amount, doc.approval_status, doc.payment_status), (350, 'Approved', 'Paid'))
        self.assertEqual(doc.payout_batch, result['batch'])

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
        center=frappe.db.get_value('Cost Center',{'company':self.company,'is_group':0,'disabled':0},'name')
        self.assertTrue(expense and cash and center,'Development accounting fixtures are required')
        frappe.db.set_value('Dieta Company Settings','DIETA-CFG-'+self.suffix,dict(generate_journal_entry=1,expense_account=expense,cost_center=center))
        frappe.db.set_value('Dieta Payment Method','DIETA-METHOD-'+self.suffix,'payment_account',cash)
        frappe.db.set_value('Employee',self.employee,'payroll_cost_center',center)
        return center

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

    def test_three_employees_two_centers_one_draft_1050(self):
        center=self.enable_accounting()
        other=frappe.db.get_value('Cost Center',{'company':self.company,'is_group':0,'disabled':0,'name':['!=',center]},'name')
        self.assertTrue(other,'Two valid development cost centers required')
        call=frappe.get_doc('Overtime Work Call',self.call_name)
        for index in (2,3):
            employee=self.employee+'-'+str(index)
            self.raw('Employee',employee,employee_name='Dieta Test '+str(index),first_name='Dieta',
                     company=self.company,status='Active',payroll_cost_center=center)
            row=call.append('employees',dict(employee=employee,employee_name='Dieta Test '+str(index)));row.db_insert()
            self.raw('Overtime Authorization',self.auth_name+'-'+str(index),docstatus=1,employee=employee,
                     employee_name='Dieta Test '+str(index),company=self.company,work_date=self.date,
                     overtime_work_call=self.call_name,authorization_start=self.date+' 20:00:00',
                     authorization_end=str(getdate()+timedelta(days=1))+' 04:00:00')
        context=service.work_call_context(self.call_name,self.date)
        rows=[dict(employee=r['employee'],amount=350,version=r['version'],reason='Meal',
                   cost_center=center if r['employee']==self.employee else other) for r in context['rows']]
        args=dict(work_call=self.call_name,work_date=self.date,rows=rows,payment_date=self.date,mode_of_payment=self.payment_method)
        preview=service.preview_payout(**args)
        payload=dict(**args,token=preview['token'],idempotency_key=str(uuid.uuid4()))
        before=frappe.db.count('GL Entry')
        result=service.confirm_payout(**payload)
        self.assertEqual(service.confirm_payout(**payload),result)
        # Employee transfers and settings edits must not rewrite the saved choice.
        frappe.db.set_value('Employee',self.employee,'payroll_cost_center',other)
        frappe.db.set_value('Dieta Company Settings','DIETA-CFG-'+self.suffix,'cost_center',other)
        accounting.generate_journal(result['batch']);accounting.generate_journal(result['batch'])
        batch=frappe.get_doc(service.BATCH,result['batch'])
        self.assertEqual(batch.cost_center_distribution,'Per Employee')
        self.assertEqual(batch.accounting_status,'Draft',batch.accounting_error)
        je=frappe.get_doc('Journal Entry',batch.journal_entry)
        self.assertEqual((je.docstatus,je.total_debit,je.total_credit),(0,1050,1050))
        debits=[r for r in je.accounts if r.debit_in_account_currency]
        self.assertEqual(len(debits),3)
        totals={}
        for row in debits:totals[row.cost_center]=totals.get(row.cost_center,0)+row.debit_in_account_currency
        self.assertEqual(totals,{center:350,other:700})
        self.assertEqual(frappe.db.count('GL Entry'),before)
        self.assertEqual(frappe.db.count('Journal Entry',{'user_remark':'Pago de dietas: '+batch.name}),1)
        self.assertEqual([r['cost_center'] for r in service.payment_history(self.call_name)[0]['rows']], [r.cost_center for r in batch.rows])

    def test_center_disabled_between_preview_and_confirmation_has_no_payment(self):
        center=self.enable_accounting();args=self.payload()
        frappe.db.set_value('Cost Center',center,'disabled',1)
        with self.assertRaisesRegex(frappe.ValidationError,'deshabilitado'):service.confirm_payout(**args)
        self.assertIsNone(service._request(self.company,self.employee,self.date))
        self.assertFalse(frappe.db.exists(service.BATCH,{'overtime_work_call':self.call_name}))

    def test_direct_api_missing_center_rejected_without_employee_fallback(self):
        self.enable_accounting();args=self.payload();args['rows'][0].pop('cost_center')
        with self.assertRaisesRegex(frappe.ValidationError,'Dieta Test'):service.confirm_payout(**args)
        self.assertIsNone(service._request(self.company,self.employee,self.date))

    def test_legacy_generation_retains_batch_center(self):
        center=self.enable_accounting();result=service.confirm_payout(**self.payload())
        batch=frappe.get_doc(service.BATCH,result['batch'])
        batch.cost_center_distribution='Legacy';batch.cost_center=center
        for row in batch.rows:row.cost_center=None
        service._save(batch)
        accounting.generate_journal(batch.name)
        batch.reload();self.assertEqual(batch.accounting_status,'Draft',batch.accounting_error)
        je=frappe.get_doc('Journal Entry',batch.journal_entry)
        self.assertEqual(je.accounts[0].cost_center,center)

if __name__=='__main__':unittest.main()
