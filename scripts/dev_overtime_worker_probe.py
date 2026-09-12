"""Dispatch or inspect one DEV worker probe. Does not enable the scheduler.

From bench/sites use ../env/bin/python ../apps/powerpro/scripts/dev_overtime_worker_probe.py dispatch
Then use inspect JOB_ID. Dispatch adds a single Redis job; its method forbids
business SQL writes and outbound effects. Never equate RQ finished with ok=true.
"""
import argparse,json,uuid
import frappe
from rq.job import Job
from rq.exceptions import NoSuchJobError
from frappe.utils.background_jobs import get_redis_conn
from powerpro.diagnostics.overtime_worker import SITE,manifest

parser=argparse.ArgumentParser();parser.add_argument('action',choices=['dispatch','inspect']);parser.add_argument('job_id',nargs='?')
args=parser.parse_args()
frappe.init(site=SITE);frappe.connect();frappe.set_user('Administrator')
try:
 assert frappe.local.site==SITE and frappe.conf.developer_mode
 if args.action=='dispatch':
  assert not frappe.db.get_single_value('DGII Payroll Settings','enable_checkin_overtime_reconciliation')
  probe_id='overtime-dev-probe-'+uuid.uuid4().hex
  job=frappe.enqueue('powerpro.diagnostics.overtime_worker.run_probe',queue='short',timeout=30,
    job_id=probe_id,deduplicate=True,probe_id=probe_id,expected_manifest=manifest())
  print(json.dumps({'job_id':job.id,'probe_id':probe_id,'status':job.get_status()},default=str))
 else:
  if not args.job_id or SITE not in args.job_id or 'overtime-dev-probe-' not in args.job_id:raise ValueError('Use the exact dispatched probe job id')
  try:job=Job.fetch(args.job_id,connection=get_redis_conn())
  except NoSuchJobError:print(json.dumps({'job_id':args.job_id,'status':'missing'}))
  else:print(json.dumps({'job_id':job.id,'status':job.get_status(),'worker':job.worker_name,'result':job.result},default=str))
finally:frappe.db.rollback();frappe.destroy()
