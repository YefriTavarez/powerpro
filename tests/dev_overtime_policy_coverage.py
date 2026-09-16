"""DEV-only policy selection regression. All fixtures roll back; no commits/mail/jobs."""
import json
import uuid
import frappe
from frappe.utils import get_datetime

frappe.init(site='igcaribe.fortabs.com');frappe.connect();frappe.set_user('Administrator')
assert frappe.local.site=='igcaribe.fortabs.com' and frappe.conf.developer_mode
from powerpro.controllers.overtime_pay_policy import get_effective_policy
from powerpro.controllers.ordinary_night import automatic_coverage_allowed, COVERAGE_PENDING
from powerpro.payroll_rules.overtime_policy_coverage import policy_names
from powerpro.payroll_rules.overtime_pay_policy import FIELDS, VERSION
from powerpro.controllers.checkin_overtime import _evidence_hash

DT='Retroactive Overtime Adjustment'
counts=['Overtime Pay Policy',DT,'Additional Salary','Salary Slip','Overtime Settlement Election','Employee Checkin']
before={d:frappe.db.count(d) for d in counts}
commit,enqueue,sendmail=frappe.db.commit,frappe.enqueue,frappe.sendmail
def forbidden(*args,**kwargs):raise AssertionError('Commit/outbound effect forbidden')
frappe.db.commit=frappe.enqueue=frappe.sendmail=forbidden
prefix='POLICY-COVERAGE-DEV-'+uuid.uuid4().hex[:8]
checks=[]
def reject(fn):
    try:fn()
    except frappe.ValidationError:return
    raise AssertionError('Expected policy rejection')
try:
    company=frappe.db.get_value('Company',{},'name')
    def create(start,end,**overrides):
        p=frappe.get_doc(dict(doctype='Overtime Pay Policy',title=prefix,company=company,
            valid_from=start,valid_until=end,approval_reference='Synthetic DEV rollback-only policy fixture',
            weekly_threshold=68,regular_percent=35,extraordinary_percent=100,night_percent=15,
            night_basis='Clock overlap',premium_combination='Additive on base hour',weekly_rest_cash=1,
            weekly_rest_percent=100,holiday_weekly_rest_mode='Single highest premium',auto_ordinary_night=1,
            **overrides))
        p.insert();p.submit();return p
    first=create('2091-08-14','2091-08-16')
    second=create('2091-08-17','2091-08-20')
    window=frappe._dict(company=company,authorization_start='2091-08-16 18:00',authorization_end='2091-08-17 06:00')
    merged=get_effective_policy(window,for_update=True)
    assert policy_names(merged)==[first.name,second.name]
    assert str(merged['policy_versions'][0]['valid_until'])==str(first.valid_until)
    checks.append('native approved adjacent policies; locked read')
    # Midnight is an exclusive end: the next date/policy is not part of the window.
    midnight=frappe._dict(window,authorization_end='2091-08-17 00:00')
    single=get_effective_policy(midnight)
    legacy=dict(frappe.db.get_value('Overtime Pay Policy',first.name,list(FIELDS),as_dict=True))
    legacy.update(holiday_weekly_rest_mode='Single highest premium',calculator_version=VERSION)
    assert single==legacy and _evidence_hash(single)==_evidence_hash(legacy)
    checks.append('exclusive midnight and unchanged legacy snapshot/hash')
    # Persist a synthetic approved snapshot fixture, like existing controller DEV tests.
    # db_insert avoids approving employee work or creating any payroll artifact.
    frozen={'input_hash':'fixture-hash','input':{'pay_policy':merged}}
    source=frappe.get_doc(dict(doctype=DT,name=prefix,docstatus=1,status='Approved',company=company,
        authorization_start=window.authorization_start,authorization_end=window.authorization_end,
        evidence_snapshot=json.dumps(frozen,default=str)))
    source.db_insert()
    native=frappe.get_doc(DT,source.name)
    assert get_effective_policy(native)==merged
    revision=frappe.copy_doc(first);revision.docstatus=0;revision.supersedes=first.name;revision.regular_percent=40
    revision.insert();revision.submit()
    assert get_effective_policy(native)==merged
    reject(lambda:get_effective_policy(window))
    checks.append('saved source pins all original revisions after rate revision; draft rejects mismatch')
    # A browser-supplied evidence_snapshot cannot replace the persisted chain.
    native.evidence_snapshot=json.dumps({'input_hash':'forged','input':{'pay_policy':{'name':revision.name}}})
    assert get_effective_policy(native)==merged
    native.evidence_snapshot=json.dumps(frozen,default=str)
    checks.append('client snapshot ignored')
    auth=frappe._dict(evidence_enrolled=1,evidence_auto_settle=1)
    result={'input':{'pay_policy':merged},'state':'Verified','night_session':{'ordinary_premium_hours':1},
            'settlement_blockers':[COVERAGE_PENDING]}
    assert automatic_coverage_allowed(auth,result)
    # Test fixture mutation only: simulate an unavailable/non-opted-in later period.
    second.db_set('auto_ordinary_night',0)
    assert not automatic_coverage_allowed(auth,result)
    second.db_set('auto_ordinary_night',1)
    second.cancel()
    reject(lambda:get_effective_policy(native,for_update=True))
    assert not automatic_coverage_allowed(auth,result)
    checks.append('every pinned policy must remain approved and opt in for automation')
    create('2092-08-14','2092-08-16');create('2092-08-18','2092-08-20')
    reject(lambda:get_effective_policy(frappe._dict(company=company,
        authorization_start='2092-08-16 18:00',authorization_end='2092-08-18 06:00')))
    checks.append('gap rejected')
    assert all(frappe.db.count(d)==before[d] for d in ['Additional Salary','Salary Slip','Overtime Settlement Election','Employee Checkin'])
    print(json.dumps({'ok':True,'checks':checks,'financial_or_checkin_writes':False}))
finally:
    frappe.db.rollback()
    frappe.db.commit,frappe.enqueue,frappe.sendmail=commit,enqueue,sendmail
    assert before=={d:frappe.db.count(d) for d in counts}
    print(json.dumps({'rollback_verified':True}))
    frappe.destroy()
