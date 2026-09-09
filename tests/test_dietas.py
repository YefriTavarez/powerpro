"""Site-free service regression tests. No Frappe installation or DB writes.

The small adapter simulates persistence/savepoints and exercises the actual API
functions. MariaDB locking and installed hooks additionally need the staging pilot.
"""
import copy
import importlib
import json
from pathlib import Path
import sys
import types
import unittest
import uuid
from datetime import date, datetime
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
package = types.ModuleType('powerpro')
package.__path__ = [str(Path(__file__).resolve().parents[1] / 'powerpro')]
sys.modules['powerpro'] = package
from powerpro.dietas.rules import money, day_key


class Record(dict):
    def __getattr__(self, key):
        return self.get(key)
    def __setattr__(self, key, value):
        self[key] = value
    def as_dict(self):
        return copy.deepcopy({k:v for k,v in self.items() if k != 'flags'})
    def append(self, key, value):
        self.setdefault(key, []).append(Record(value))
    def check_permission(self, action):
        if self.get('deny_read'):
            raise PermissionError('Denied')
    def save(self, **kwargs):
        self.name = self.get('name') or self.get('day_key') or f'{self.doctype}-{len(store)}'
        self.modified = str(next(counter))
        store[(self.doctype, self.name)] = self.as_dict()
        return self
    def insert(self, **kwargs):
        if self.doctype == 'Journal Entry' and fail_je[0]:
            raise ValueError('Accounting unavailable')
        return self.save(**kwargs)
    def reload(self):
        self.update(copy.deepcopy(store[(self.doctype, self.name)]))
        return self
    def is_new(self):
        return (self.doctype, self.name) not in store


def record(value):
    if isinstance(value, dict):
        return Record({k: record(v) for k,v in value.items()})
    if isinstance(value, list):
        return [record(v) for v in value]
    return value


def put(dt, name, **kwargs):
    value = record(dict(doctype=dt, name=name, modified='0', docstatus=0, **kwargs))
    store[(dt,name)] = copy.deepcopy(value)
    return value


def matches(doc, filters):
    for key, value in (filters or {}).items():
        if isinstance(value, list):
            if value[0] == 'in' and doc.get(key) not in value[1]: return False
        elif str(doc.get(key)) != str(value): return False
    return True


def get_all(dt, filters=None, pluck=None, fields=None, **kwargs):
    values = [v for (t,n),v in store.items() if t==dt and matches(v,filters)]
    if pluck: return [v.get(pluck) for v in values]
    return [record({f:v.get(f) for f in fields}) if fields else record(copy.deepcopy(v)) for v in values]


def get_doc(dt, name=None, **kwargs):
    value = record(copy.deepcopy(store[(dt,name)]))
    value.flags = Record()
    return value


class DB:
    def get_values(self, dt, filters=None, fieldname='name', pluck=False, as_dict=False, for_update=False):
        return get_all(dt, filters, pluck=fieldname if pluck else None, fields=fieldname if isinstance(fieldname,list) else [fieldname])
    def get_value(self, dt, name, fields, for_update=False, **kwargs):
        if for_update: locks.append((dt,name))
        docs = get_all(dt, name if isinstance(name,dict) else {'name':name})
        if not docs: return None
        value = docs[0]
        if isinstance(fields,list): return record({f:value.get(f) for f in fields})
        return value.get(fields)
    def exists(self, dt, name):
        if dt=='DocType': return True
        return self.get_value(dt,name,'name')
    def savepoint(self,name):
        snapshots[name] = copy.deepcopy(store)
    def rollback(self, save_point=None):
        store.clear(); store.update(copy.deepcopy(snapshots[save_point]))
    def set_value(self,dt,name,values,**kwargs):
        store[(dt,name)].update(values)
    def escape(self,value): return "'"+value.replace("'","''")+"'"
    def commit(self): pass


fake = types.ModuleType('frappe')
fake.PermissionError = PermissionError
fake.throw = lambda msg, exc=ValueError, **kw: (_ for _ in ()).throw(exc(msg))
fake.whitelist = lambda *a, **k: lambda fn: fn
fake.parse_json = json.loads
fake.get_all = get_all
fake.get_doc = get_doc
fake.new_doc = lambda dt: Record(doctype=dt, docstatus=0, flags=Record())
fake.get_roles = lambda user=None: roles.get(user or fake.session.user, [])
fake.has_permission = lambda *a, **k: True
fake.log_error = lambda *a, **k: None
fake.enqueue = lambda *a, **k: queued.append((a,k))
fake.session = Record(user='manager')
fake.db = DB()
fake.db.after_commit = Record(add=lambda fn: callbacks.append(fn))
utils = types.ModuleType('frappe.utils')
utils.cint = lambda x: int(x or 0)
utils.getdate = lambda x=None: date.fromisoformat(str(x)) if x else date(2026,9,9)
utils.now_datetime = lambda: datetime(2026,9,9,18)
perms = types.ModuleType('frappe.permissions')
perms.get_user_permissions = lambda user: restrictions.get(user,{})
model = types.ModuleType('frappe.model'); document = types.ModuleType('frappe.model.document')
document.Document = object
fake_modules = patch.dict(sys.modules, {'frappe':fake,'frappe.utils':utils,'frappe.permissions':perms,'frappe.model':model,'frappe.model.document':document})
fake_modules.start()
service = importlib.import_module('powerpro.dietas.service')
access = importlib.import_module('powerpro.dietas.permissions')
accounting = importlib.import_module('powerpro.dietas.accounting')
hooks = importlib.import_module('powerpro.dietas.hooks')
documents = importlib.import_module('powerpro.dietas.documents')


class DietasTest(unittest.TestCase):
    def setUp(self):
        global store,snapshots,roles,restrictions,locks,callbacks,queued,counter,fail_je
        import itertools
        store={}; snapshots={};roles={'manager':['HR Manager']};restrictions={};locks=[];callbacks=[];queued=[];counter=itertools.count(1);fail_je=[False]
        fake.session.user='manager'
        put('Company','IGC',default_currency='DOP')
        put('Dieta Company Settings','cfg',parent='IGC Settings',company='IGC',enabled=1,default_amount=300,generate_journal_entry=0,expense_account='Meals',cost_center='Main')
        put('Dieta Payment Method','cash',parent='IGC Settings',company='IGC',mode_of_payment='Cash',payment_account='Cash')
        put('Account','Meals',company='IGC',is_group=0,disabled=0,root_type='Expense',account_currency='DOP')
        put('Account','Cash',company='IGC',is_group=0,disabled=0,account_type='Cash',account_currency='DOP')
        put('Cost Center','Main',company='IGC')
        call=put('Overtime Work Call','CALL',company='IGC',dates=[{'work_date':'2026-09-09','allows_dieta':1}],employees=[{'employee':'E1'},{'employee':'E2'}])
        call.docstatus=1;store[('Overtime Work Call','CALL')]=call
        for emp in ('E1','E2'):
            put('Employee',emp,employee_name=emp,company='IGC',department='Production',status='Active',expense_approver='approver',user_id=emp+'@example.com')
            auth=put('Overtime Authorization','AUTH-'+emp,employee=emp,work_date='2026-09-09',overtime_work_call='CALL',authorization_start='2026-09-09 20:00',authorization_end='2026-09-10 04:00')
            auth.docstatus=1;store[('Overtime Authorization',auth.name)]=auth
    def selected(self, employees=('E1','E2')):
        rows=service.work_call_context('CALL','2026-09-09')['rows']
        return [dict(employee=r['employee'],amount=r['amount'],version=r['version'],reason='') for r in rows if r['employee'] in employees]
    def payload(self, employees=('E1','E2'), **override):
        args=dict(work_call='CALL',work_date='2026-09-09',rows=self.selected(employees),payment_date='2026-09-09',mode_of_payment='Cash')
        args.update(override)
        preview=service.preview_payout(**args)
        return dict(**args,token=preview['token'],idempotency_key=str(uuid.uuid4()))
    def pay(self,employees=('E1','E2')):
        return service.confirm_payout(**self.payload(employees))
    def test_roster_without_request_creates_approved_paid_requests(self):
        result=self.pay();self.assertEqual(result['total'],600)
        self.assertEqual(len(get_all(service.REQUEST)),2)
        for req in get_all(service.REQUEST):
            self.assertEqual((req.origin,req.approval_status,req.payment_status),('Manager','Approved','Paid'))
            self.assertEqual(req.paid_by,'manager');self.assertIn('approve_and_pay',req.audit_log)
        self.assertEqual([x for x in locks if x[0]=='Employee'], [('Employee','E1'),('Employee','E2')])
    def test_selected_subset_only(self):
        self.pay(('E1',));self.assertFalse(service._request('IGC','E2','2026-09-09'))
    def test_same_idempotency_key_returns_same_batch(self):
        payload=self.payload();a=service.confirm_payout(**payload);b=service.confirm_payout(**payload)
        self.assertEqual(a,b);self.assertEqual(len(get_all(service.BATCH)),1)
    def test_key_reuse_different_payload_rejected(self):
        payload=self.payload();service.confirm_payout(**payload);payload['reference']='changed'
        with self.assertRaises(ValueError): service.confirm_payout(**payload)
    def test_new_key_cannot_pay_again(self):
        self.pay()
        with self.assertRaises(ValueError):self.pay()
    def test_stale_amount_fails_before_any_write(self):
        args=self.payload();store[('Dieta Company Settings','cfg')]['default_amount']=400
        with self.assertRaises(ValueError):service.confirm_payout(**args)
        self.assertFalse(get_all(service.REQUEST));self.assertFalse(get_all(service.BATCH))
    def test_second_payer_stale_preview(self):
        args=self.payload();self.pay();fake.session.user='other';roles['other']=['HR Manager']
        with self.assertRaises(ValueError):service.confirm_payout(**args)
        self.assertEqual(len(get_all(service.BATCH)),1)
    def test_atomic_rollback_after_request_write_failure(self):
        args=self.payload();original=service._save
        def failing(doc,*a,**k):
            if doc.doctype==service.BATCH:raise RuntimeError('storage failure')
            return original(doc,*a,**k)
        with patch.object(service,'_save',side_effect=failing),self.assertRaises(RuntimeError):service.confirm_payout(**args)
        self.assertFalse(get_all(service.REQUEST))
    def test_authorization_cancelled_after_preview_blocks_payment(self):
        args=self.payload();store[('Overtime Authorization','AUTH-E2')]['docstatus']=2
        with self.assertRaises(ValueError):service.confirm_payout(**args)
        self.assertFalse(get_all(service.REQUEST))
    def test_unmarked_date_blocks(self):
        store[('Overtime Work Call','CALL')]['dates'][0]['allows_dieta']=0
        with self.assertRaises(ValueError):service.preview_payout(**dict(work_call='CALL',work_date='2026-09-09',rows=[{'employee':'E1','version':'x','amount':300}],payment_date='2026-09-09',mode_of_payment='Cash'))
    def test_self_payment_denied_even_hr(self):
        store[('Employee','E1')]['user_id']='manager'
        self.assertEqual([r['employee'] for r in service.work_call_context('CALL','2026-09-09')['rows']],['E2'])
        with self.assertRaises(PermissionError):service._employee('E1')
    def test_approver_scope(self):
        fake.session.user='approver';store[('Employee','E2')]['expense_approver']='another'
        self.assertEqual(len(self.selected()),1)
        with self.assertRaises(PermissionError):service._employee('E2')
    def test_company_user_permission_restricts_hr(self):
        restrictions['manager']={'Company':[{'doc':'OTHER'}]}
        self.assertFalse(service.work_call_context('CALL')['enabled'])
    def test_employee_self_service_and_manager_reuse(self):
        fake.session.user='E1@example.com'
        result=service.request_dieta('AUTH-E1','food');self.assertEqual(len(service.my_dietas()['requests']),1)
        with self.assertRaises(PermissionError):service.request_dieta('AUTH-E2')
        fake.session.user='manager';self.pay(('E1',));self.assertEqual(len(get_all(service.REQUEST)),1)
        self.assertEqual(get_doc(service.REQUEST,result['request']).origin,'Employee')
    def test_duplicate_self_request_returns_same_record(self):
        fake.session.user='E1@example.com';a=service.request_dieta('AUTH-E1');b=service.request_dieta('AUTH-E1')
        self.assertEqual(a,b)
    def test_override_requires_reason(self):
        rows=self.selected();rows[0]['amount']=500
        with self.assertRaises(ValueError):self.payload(rows=rows)
        rows[0]['reason']='Extra meal';result=service.confirm_payout(**self.payload(rows=rows));self.assertEqual(result['total'],800)
    def test_reject_reconsider_approve_then_pay(self):
        fake.session.user='E1@example.com';service.request_dieta('AUTH-E1');fake.session.user='manager'
        service.manage_requests('CALL','2026-09-09',self.selected(('E1',)),'reject','Not eligible today')
        with self.assertRaises(ValueError):self.pay(('E1',))
        service.manage_requests('CALL','2026-09-09',self.selected(('E1',)),'reconsider','Reviewed')
        service.manage_requests('CALL','2026-09-09',self.selected(('E1',)),'approve')
        self.pay(('E1',))
    def test_approved_amount_change_requires_reconsideration(self):
        fake.session.user='E1@example.com';service.request_dieta('AUTH-E1');fake.session.user='manager'
        service.manage_requests('CALL','2026-09-09',self.selected(('E1',)),'approve')
        with self.assertRaises(ValueError):service.manage_requests('CALL','2026-09-09',self.selected(('E1',)),'amount','Change')
    def test_full_payment_not_partial(self):
        self.pay(('E1',));req=service._request('IGC','E1','2026-09-09')
        self.assertEqual(req.amount,300);self.assertEqual(req.payment_status,'Paid')
        with self.assertRaises(ValueError):service.manage_requests('CALL','2026-09-09',self.selected(('E1',)),'reconsider','Change')
    def test_default_snapshot_survives_configuration_change(self):
        fake.session.user='E1@example.com';service.request_dieta('AUTH-E1');fake.session.user='manager'
        store[('Dieta Company Settings','cfg')]['default_amount']=700
        self.assertEqual(self.selected(('E1',))[0]['amount'],300)
    def test_future_payment_rejected(self):
        with self.assertRaises(ValueError):self.payload(payment_date='2026-09-10')
    def test_accounting_disabled_no_callback_or_journal(self):
        self.pay();self.assertFalse(callbacks);self.assertFalse(get_all('Journal Entry'))
    def test_accounting_enabled_draft_and_idempotent_generator(self):
        store[('Dieta Company Settings','cfg')]['generate_journal_entry']=1
        result=self.pay();self.assertEqual(len(callbacks),1);self.assertFalse(get_all('Journal Entry'))
        accounting.generate_journal(result['batch']);accounting.generate_journal(result['batch'])
        jes=get_all('Journal Entry');self.assertEqual(len(jes),1);self.assertEqual(jes[0].docstatus,0)
        self.assertEqual(sum(r.debit_in_account_currency or 0 for r in jes[0].accounts),600)
        self.assertEqual(sum(r.credit_in_account_currency or 0 for r in jes[0].accounts),600)
    def test_accounting_failure_preserves_payout_retry_succeeds(self):
        store[('Dieta Company Settings','cfg')]['generate_journal_entry']=1
        result=self.pay();fail_je[0]=True;accounting.generate_journal(result['batch'])
        self.assertEqual(get_doc(service.BATCH,result['batch']).accounting_status,'Error')
        self.assertTrue(all(r.payment_status=='Paid' for r in get_all(service.REQUEST)))
        fail_je[0]=False;accounting.generate_journal(result['batch']);self.assertEqual(len(get_all('Journal Entry')),1)
    def test_toggle_does_not_post_old_batch(self):
        result=self.pay();store[('Dieta Company Settings','cfg')]['generate_journal_entry']=1
        accounting.generate_journal(result['batch']);self.assertFalse(get_all('Journal Entry'))
    def test_unauthorized_accounting_retry(self):
        result=self.pay();fake.session.user='E1@example.com'
        with self.assertRaises(PermissionError):accounting.retry_accounting(result['batch'])
    def test_journal_cancel_does_not_reverse_payment(self):
        store[('Dieta Company Settings','cfg')]['generate_journal_entry']=1
        result=self.pay();accounting.generate_journal(result['batch']);je=get_doc('Journal Entry',get_all('Journal Entry')[0].name);je.docstatus=2;accounting.journal_status(je)
        self.assertEqual(get_doc(service.BATCH,result['batch']).accounting_status,'Cancelled')
        self.assertTrue(all(r.payment_status=='Paid' for r in get_all(service.REQUEST)))
    def test_source_cancellation_preserves_paid_audit(self):
        self.pay(('E1',));hooks.authorization_cancelled(get_doc('Overtime Authorization','AUTH-E1'))
        req=service._request('IGC','E1','2026-09-09');self.assertEqual(req.payment_status,'Paid');self.assertEqual(req.review_required,1)
    def test_source_cancellation_cancels_unpaid(self):
        fake.session.user='E1@example.com';service.request_dieta('AUTH-E1');fake.session.user='manager'
        hooks.authorization_cancelled(get_doc('Overtime Authorization','AUTH-E1'))
        self.assertEqual(service._request('IGC','E1','2026-09-09').approval_status,'Cancelled')
    def test_attendance_flags_paid_for_review(self):
        self.pay(('E1',));auth=get_doc('Overtime Authorization','AUTH-E1');auth.reconciliation_status='Absent';hooks.flag_attendance_review(auth)
        self.assertEqual(service._request('IGC','E1','2026-09-09').review_required,1)
    def test_mixed_scope_batch_is_not_disclosed(self):
        self.pay();fake.session.user='approver';store[('Employee','E2')]['expense_approver']='another'
        self.assertEqual(service.payment_history('CALL'),[])
    def test_cross_midnight_retains_work_date(self):
        self.pay(('E1',));self.assertEqual(str(service._request('IGC','E1','2026-09-09').work_date),'2026-09-09')
    def test_currency_invalid_values(self):
        for value in ('NaN','Infinity',0,-2,'not-money'):
            with self.assertRaises(ValueError):money(value)
    def test_day_key_ignores_source_call(self):
        self.assertEqual(day_key('IGC','E1','2026-09-09'),day_key('IGC','E1',date(2026,9,9)))
    def test_permission_hook_uses_frappe_ptype(self):
        self.pay(('E1',));req=service._request('IGC','E1','2026-09-09')
        self.assertTrue(access.request_permission(req,ptype='read'))
        self.assertFalse(access.request_permission(req,ptype='write'))
        self.assertFalse(access.request_permission(req,ptype='create'))
    def test_generic_record_write_delete_denied(self):
        doc=types.SimpleNamespace(flags=Record())
        with self.assertRaises(PermissionError):documents.ManagedDietaDocument.validate(doc)
        with self.assertRaises(PermissionError):documents.ManagedDietaDocument.on_trash(doc)
    def test_no_payroll_or_claim_records_created(self):
        self.pay()
        for dt in ('Additional Salary','Salary Slip','Expense Claim','Employee Advance'):
            self.assertFalse(get_all(dt))
    def test_disabled_feature_keeps_history_accessible(self):
        self.pay();store[('Dieta Company Settings','cfg')]['enabled']=0
        context=service.work_call_context('CALL');self.assertTrue(context['enabled']);self.assertFalse(context['active']);self.assertEqual(context['summary']['paid'],600)
    def test_correction_requires_accounting_resolution(self):
        store[('Dieta Company Settings','cfg')]['generate_journal_entry']=1
        result=self.pay();accounting.generate_journal(result['batch'])
        with self.assertRaises(ValueError):accounting.reverse_erroneous_payout(result['batch'],'Clerical mistake')
    def test_correction_without_accounting_preserves_audit(self):
        result=self.pay();accounting.reverse_erroneous_payout(result['batch'],'Clerical mistake')
        self.assertEqual(get_doc(service.BATCH,result['batch']).status,'Reversed')
        self.assertTrue(all(r.payment_status=='Unpaid' and 'reverse_erroneous_payment' in r.audit_log for r in get_all(service.REQUEST)))

if __name__=='__main__': unittest.main()
