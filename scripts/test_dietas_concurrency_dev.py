"""Two real DB sessions; opt-in committed synthetic fixtures, exact cleanup.

Never production. Unlike the rollback-only suite, concurrency fixtures must be
visible to both connections. No mail or background jobs are allowed. Accounting
is disabled. A fresh synthetic employee isolates every request and payout.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
import json
import os
from pathlib import Path
import runpy
import threading
import uuid
from unittest.mock import patch
from urllib.parse import urlsplit

import frappe

parser=argparse.ArgumentParser()
parser.add_argument('--site',required=True)
parser.add_argument('--sites-path',required=True)
parser.add_argument('--company',required=True)
parser.add_argument('--confirm-development-committed-fixtures',action='store_true',required=True)
a=parser.parse_args()
if a.site in ('igcaribe.com','igcaribe.erpnext.com'): raise SystemExit('Refusing production')
frappe.init(site=a.site,sites_path=a.sites_path)
if not frappe.conf.developer_mode or urlsplit(frappe.conf.get('host_name') or '').hostname in ('igcaribe.com','www.igcaribe.com'):
    raise SystemExit('Verified development configuration required')
frappe.connect();frappe.set_user('Administrator')
os.environ['POWERPRO_DIETA_DEV_TESTS']='1';os.environ['POWERPRO_DIETA_TEST_COMPANY']=a.company
from powerpro.dietas import service
ns=runpy.run_path(str(Path(__file__).resolve().parents[1]/'tests/test_dietas_db.py'),run_name='dieta_concurrency_fixture')
Fixture=ns['DietaDatabaseTest']


def blocked(*args,**kwargs): raise AssertionError('No email or background job during concurrency testing')


def cleanup(fixture, calls, old_series):
    requests=frappe.get_all(service.REQUEST,filters={'employee':fixture.employee},pluck='name')
    batches=frappe.get_all(service.BATCH,filters={'overtime_work_call':['in',calls]},pluck='name')
    names=requests+batches+calls+[fixture.employee,fixture.auth_name,fixture.auth_name+'-B']
    for dt, field in [('Version','docname'),('Comment','reference_name'),('DocShare','share_name'),('ToDo','reference_name')]:
        if names: frappe.db.delete(dt,{field:['in',names]})
    if batches:
        frappe.db.delete('Dieta Payout Row',{'parent':['in',batches]})
        frappe.db.delete(service.BATCH,{'name':['in',batches]})
    if requests:frappe.db.delete(service.REQUEST,{'name':['in',requests]})
    frappe.db.delete('Overtime Authorization',{'employee':fixture.employee})
    for dt in ['Overtime Work Call Employee','Overtime Work Call Date']:
        frappe.db.delete(dt,{'parent':['in',calls]})
    frappe.db.delete('Overtime Work Call',{'name':['in',calls]})
    frappe.db.delete('Employee',{'name':fixture.employee})
    frappe.db.delete('Dieta Company Settings',{'name':'DIETA-CFG-'+fixture.suffix})
    frappe.db.delete('Dieta Payment Method',{'name':'DIETA-METHOD-'+fixture.suffix})
    current=dict(frappe.db.sql("select name, current from tabSeries where name like 'DIETA-PAY-%' for update"))
    for key,value in current.items():
        # Never rewind a series if somebody outside this test has advanced it.
        expected=old_series.get(key,0)+len(batches)
        if value!=expected:raise AssertionError('Unexpected external series activity; manual review required')
        if key in old_series:frappe.db.sql('update tabSeries set current=%s where name=%s',(old_series[key],key))
        else:frappe.db.sql('delete from tabSeries where name=%s',(key,))
    frappe.db.commit()
    assert not frappe.db.exists('Employee',fixture.employee)
    assert not frappe.db.exists(service.REQUEST,{'employee':fixture.employee})
    assert not frappe.db.exists(service.BATCH,{'overtime_work_call':['in',calls]})


def worker(payload, barrier):
    frappe.init(site=a.site,sites_path=a.sites_path);frappe.connect();frappe.set_user('Administrator')
    try:
        barrier.wait(timeout=15)
        result=service.confirm_payout(**payload)
        frappe.db.commit()
        return {'success':True,'batch':result['batch']}
    except Exception as exc:
        frappe.db.rollback()
        return {'success':False,'error_type':type(exc).__name__,'error':str(exc)}
    finally:frappe.destroy()


results=[]
try:
    with ExitStack() as stack:
        stack.enter_context(patch.object(frappe,'sendmail',blocked))
        stack.enter_context(patch.object(frappe,'enqueue',return_value=None))
        for scenario in ('same_work_call','different_work_calls'):
            if any(frappe.db.exists(dt, {'company':a.company}) for dt in ('Dieta Company Settings', 'Dieta Payment Method')):
                raise AssertionError('This test requires no existing dieta configuration for the chosen development company')
            old_series=dict(frappe.db.sql("select name, current from tabSeries where name like 'DIETA-PAY-%'"))
            fixture=Fixture();fixture.setUp();calls=[fixture.call_name]
            try:
                first=fixture.payload()
                if scenario=='different_work_calls':
                    second_call=fixture.call_name+'-B';calls.append(second_call)
                    call=fixture.raw('Overtime Work Call',second_call,docstatus=1,company=fixture.company,
                        reason='Isolated concurrency test B',status='Authorized',from_date=fixture.date,to_date=fixture.date)
                    call.append('dates',dict(work_date=fixture.date,start_time='18:00:00',end_time='19:00:00',allows_dieta=1)).db_insert()
                    call.append('employees',dict(employee=fixture.employee,employee_name='Dieta Test')).db_insert()
                    fixture.raw('Overtime Authorization',fixture.auth_name+'-B',docstatus=1,employee=fixture.employee,
                        employee_name='Dieta Test',company=fixture.company,work_date=fixture.date,overtime_work_call=second_call,
                        authorization_start=fixture.date+' 18:00:00',authorization_end=fixture.date+' 19:00:00')
                    original=fixture.call_name;fixture.call_name=second_call
                    second=fixture.payload();fixture.call_name=original
                else:
                    second={**first,'idempotency_key':str(uuid.uuid4())}
                frappe.db.commit()
                barrier=threading.Barrier(2)
                with ThreadPoolExecutor(max_workers=2) as pool:
                    one=pool.submit(worker,first,barrier);two=pool.submit(worker,second,barrier)
                    outcomes=[one.result(timeout=40),two.result(timeout=40)]
                frappe.db.rollback()  # discard any old consistent-read snapshot
                winners=[r for r in outcomes if r['success']]
                assert len(winners)==1,outcomes
                assert frappe.db.count(service.REQUEST,{'employee':fixture.employee})==1
                assert frappe.db.count(service.BATCH,{'overtime_work_call':['in',calls]})==1
                results.append({'scenario':scenario,'outcomes':outcomes,'requests':1,'batches':1})
                print(json.dumps(results[-1],ensure_ascii=False),flush=True)
            finally:
                frappe.db.rollback()
                cleanup(fixture,calls,old_series)
        print('CONCURRENCY_TESTS_PASSED_AND_FIXTURES_REMOVED',flush=True)
finally:
    frappe.db.rollback();frappe.destroy()
