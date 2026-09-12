"""DEV probe contract: a stale manifest must fail without generating Error Log."""
import uuid
import frappe
from powerpro.diagnostics.overtime_worker import run_probe,manifest,COUNTS,SITE
frappe.init(site=SITE);frappe.connect();frappe.set_user('Administrator')
assert frappe.local.site==SITE and frappe.conf.developer_mode
before={dt:frappe.db.count(dt) for dt in COUNTS}
try:
 good=run_probe('overtime-dev-probe-'+uuid.uuid4().hex,manifest())
 assert good['ok'] and good['paused_result']=='Paused'
 stale=run_probe('overtime-dev-probe-'+uuid.uuid4().hex,{})
 assert stale['ok'] is False and stale['error_type']=='AssertionError'
 frappe.set_user('Guest')
 try:run_probe('overtime-dev-probe-'+uuid.uuid4().hex,{})
 except frappe.PermissionError:pass
 else:raise AssertionError('Guest ran an operator diagnostic')
 print('WORKER_PROBE_CONTRACT: correct manifest passes, stale manifest returns explicit failure, Guest refused')
finally:
 frappe.set_user('Administrator');frappe.db.rollback()
 after={dt:frappe.db.count(dt) for dt in COUNTS};assert before==after,(before,after)
 print('WORKER_PROBE_COUNTS_UNCHANGED',after);frappe.db.rollback();frappe.destroy()
