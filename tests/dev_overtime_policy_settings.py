"""DEV-only native settings/policy revisions; all writes rolled back."""
import json
import uuid
import frappe
from frappe.utils import get_datetime

frappe.init(site='igcaribe.fortabs.com'); frappe.connect(); frappe.set_user('Administrator')
assert frappe.local.site == 'igcaribe.fortabs.com' and frappe.conf.developer_mode
from powerpro.controllers.overtime_policy_settings import load_version, SETTING_MAP
from powerpro.controllers.overtime_pay_policy import get_effective_policy
from powerpro.payroll_rules.overtime_pay_policy import classify_night_session

counts = ['Overtime Pay Policy','Additional Salary','Salary Slip','Version','Comment','Error Log']
before = {dt:frappe.db.count(dt) for dt in counts}
settings_before = frappe.db.get_singles_dict('DGII Payroll Settings')
commit, enqueue, sendmail = frappe.db.commit, frappe.enqueue, frappe.sendmail
def forbidden(*args, **kwargs): raise AssertionError('Outbound effect or commit forbidden')
frappe.db.commit = frappe.enqueue = frappe.sendmail = forbidden

def fail(action, error=frappe.ValidationError):
    point='policy_'+uuid.uuid4().hex[:8]
    frappe.db.savepoint(point)
    try: action()
    except error: frappe.db.rollback(save_point=point)
    else: raise AssertionError('Expected rejection')

try:
    company=frappe.db.get_value('Company', {}, 'name')
    settings=frappe.get_single('DGII Payroll Settings')
    settings.manage_overtime_pay_policy=0
    settings.save()
    assert frappe.db.count('Overtime Pay Policy') == before['Overtime Pay Policy']
    settings.update(dict(manage_overtime_pay_policy=1, overtime_policy_company=company,
        overtime_policy_from='2035-01-01', overtime_policy_until='2035-12-31',
        overtime_policy_version=None, overtime_policy_whole_night=0,
        overtime_policy_weekly_threshold=68, overtime_policy_regular_percent=35,
        overtime_policy_extraordinary_percent=100, overtime_policy_night_percent=15,
        overtime_policy_weekly_rest_percent=100, overtime_policy_weekly_rest_cash=0,
        overtime_policy_compensatory=0, overtime_policy_auto_ordinary_night=0))
    settings.save(); settings.reload(); first=settings.overtime_policy_version
    assert first and frappe.db.get_value('Overtime Pay Policy', first, 'docstatus') == 1
    assert frappe.db.get_value('Overtime Pay Policy', first, 'approved_by') == 'Administrator'
    settings.save(); settings.reload()
    assert settings.overtime_policy_version == first
    assert frappe.db.count('Overtime Pay Policy') == before['Overtime Pay Policy']+1
    window=frappe._dict(company=company,authorization_start='2035-06-01 18:00',authorization_end='2035-06-02 00:00')
    assert get_effective_policy(window)['name']==first
    settings.overtime_policy_whole_night=1;settings.save();settings.reload();second=settings.overtime_policy_version
    assert second!=first
    assert frappe.db.get_value('Overtime Pay Policy',second,'supersedes')==first
    assert frappe.db.get_value('Overtime Pay Policy',first,'night_basis')=='Clock overlap'
    assert get_effective_policy(window)['name']==second
    hours=classify_night_session([{'start':window.authorization_start,'end':window.authorization_end}],
        [{'start':'2035-06-01 20:00','end':window.authorization_end}],basis=get_effective_policy(window)['night_basis'])
    assert (hours['premium_hours'],hours['ordinary_premium_hours'])==(6,2)
    # Multiple revisions remain a single active period, and unchanged saves do not duplicate.
    settings.overtime_policy_weekly_rest_cash=1;settings.overtime_policy_auto_ordinary_night=1
    settings.save();settings.reload();third=settings.overtime_policy_version
    assert get_effective_policy(window)['name']==third
    assert frappe.db.get_value('Overtime Pay Policy',third,'auto_ordinary_night')==1
    loaded=load_version(third)
    assert loaded['overtime_policy_whole_night']==1 and loaded['overtime_policy_weekly_rest_cash']==1
    settings.update(loaded);settings.save();settings.reload()
    assert settings.overtime_policy_version==third
    # Stale editors cannot branch a period or silently republish obsolete settings.
    stale=frappe.get_single('DGII Payroll Settings');stale.update(load_version(first))
    fail(stale.save)
    invalid=frappe.get_single('DGII Payroll Settings');invalid.overtime_policy_night_percent=14
    fail(invalid.save)
    assert frappe.db.get_single_value('DGII Payroll Settings','overtime_policy_night_percent')==15
    assert frappe.db.count('Overtime Pay Policy')==before['Overtime Pay Policy']+3
    invalid=frappe.get_single('DGII Payroll Settings');invalid.overtime_policy_from='2035-06-01'
    fail(invalid.save)
    old=frappe.get_doc('Overtime Pay Policy',first);old.night_percent=20
    fail(old.save)
    fail(lambda:frappe.get_doc('Overtime Pay Policy',first).cancel())
    # The compensatory switches carry their conversion rules into the effective policy.
    settings=frappe.get_single('DGII Payroll Settings')
    settings.update(dict(overtime_policy_compensatory=1,
        overtime_policy_leave_type=frappe.db.get_value('Leave Type',{'is_compensatory':1},'name'),
        overtime_policy_hours_per_day=8,overtime_policy_leave_increment=.5,
        overtime_policy_rest_factor=1,overtime_policy_rest_duration=36,overtime_policy_rest_credit=8))
    settings.save();settings.reload();third=settings.overtime_policy_version
    effective=get_effective_policy(window)
    assert effective['enable_compensatory']==1 and effective['hours_per_leave_day']==8
    assert effective['weekly_rest_credit_hours']==8 and effective['leave_increment']==.5
    # New disjoint dates publish a separate active period; crossing periods is explicit.
    settings=frappe.get_single('DGII Payroll Settings');settings.overtime_policy_from='2036-01-01';settings.overtime_policy_until='2036-12-31'
    settings.save();settings.reload();fourth=settings.overtime_policy_version
    assert fourth!=third and not frappe.db.get_value('Overtime Pay Policy',fourth,'supersedes')
    fail(lambda:get_effective_policy(frappe._dict(company=company,
        authorization_start='2035-12-31 22:00',authorization_end='2036-01-01 02:00')))
    assert get_effective_policy(frappe._dict(company='not-this-company',authorization_start=window.authorization_start,
        authorization_end=window.authorization_end)) is None
    # Turning publication off is not an implicit cancellation or payroll action.
    settings.manage_overtime_pay_policy=0;settings.overtime_policy_whole_night=0;settings.save()
    assert get_effective_policy(window)['name']==third
    frappe.set_user('Guest')
    fail(lambda:load_version(third),frappe.PermissionError)
    fail(lambda:frappe.get_single('DGII Payroll Settings').save(),frappe.PermissionError)
    frappe.set_user('Administrator')
    assert frappe.db.count('Additional Salary')==before['Additional Salary']
    assert frappe.db.count('Salary Slip')==before['Salary Slip']
    assert frappe.db.get_single_value('DGII Payroll Settings','enable_checkin_overtime_reconciliation')==int(settings_before.get('enable_checkin_overtime_reconciliation') or 0)
    print(json.dumps({'ok':True,'checks':['native Single save publishes','idempotent save','clock and whole session',
        'linear revisions','stale editor denied','rate floor','partial overlap denied','company and date isolation',
        'immutable old version','compensatory conversion published','Guest denied','no financial output','disabled does not cancel']}))
finally:
    frappe.set_user('Administrator');frappe.db.rollback()
    frappe.db.commit,frappe.enqueue,frappe.sendmail=commit,enqueue,sendmail
    assert before=={dt:frappe.db.count(dt) for dt in counts}
    assert settings_before==frappe.db.get_singles_dict('DGII Payroll Settings')
    print(json.dumps({'rollback_verified':True,'counts':before}))
    frappe.destroy()
