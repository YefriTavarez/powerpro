"""Policy and access regression checks using the existing site-free adapter."""
import runpy
from pathlib import Path
import unittest
from unittest.mock import patch
adapter=runpy.run_path(str(Path(__file__).with_name('test_manual_overtime.py')),run_name='auto_adapter')
from powerpro.controllers import automatic_overtime as auto
from powerpro.controllers.overtime_settlement import settlement_hours
R=adapter['Record']
class AutomaticPolicyTests(unittest.TestCase):
 def test_presumed_hours_never_require_fabricated_verification(self):
  self.assertEqual(settlement_hours(R(reconciliation_source='Presumed Attendance',auto_enrolled=1,presumed_hours=5,verified_hours=0)),5)
  self.assertEqual(settlement_hours(R(reconciliation_source='Presumed Attendance',auto_enrolled=0,presumed_hours=5,verified_hours=0)),0)
 def test_cash_date_policies(self):
  call=R(planned_settlement='Cash',automatic_payroll_date='2026-09-30')
  self.assertEqual(str(auto._payroll_date(call,'2026-09-13','Work Date')),'2026-09-13')
  self.assertEqual(str(auto._payroll_date(call,'2026-09-13','Month End')),'2026-09-30')
  self.assertEqual(str(auto._payroll_date(call,'2026-09-13','Work Call Date')),'2026-09-30')
  with self.assertRaises(ValueError):auto._payroll_date(call,'2026-10-01','Work Call Date')
 def test_assigned_approver_or_configured_roles(self):
  settings=R(overtime_exception_roles='Custom Approver')
  with patch.object(auto.frappe,'get_roles',return_value=['System Manager']):
   self.assertFalse(auto._allowed(R(approver='another'),settings))
   self.assertTrue(auto._allowed(R(approver=auto.frappe.session.user),settings))
  with patch.object(auto.frappe,'get_roles',return_value=['Custom Approver']):self.assertTrue(auto._allowed(R(approver='another'),settings))
 def test_generic_save_cannot_forge_enrollment(self):
  doc=R(doctype=auto.AUTH,auto_enrolled=1)
  with self.assertRaises(ValueError):auto.protect_fields(doc)
 def test_reason_and_enrollment_required(self):
  doc=R(name='AUTH',auto_enrolled=1,modified='1',settlement_status='Pending')
  with self.assertRaises(ValueError):auto._exception_input(doc,'Mark Absent','',None)
  doc.auto_enrolled=0
  with self.assertRaises(ValueError):auto._exception_input(doc,'Mark Absent','Reason',None)
 def test_pending_correction_requires_retry_not_overwrite(self):
  with self.assertRaises(ValueError):auto._exception_input(R(auto_status='Correction Pending'),'Mark Absent','Reason',None)
 def test_future_hours_cannot_be_certified(self):
  doc=R(name='AUTH',auto_enrolled=1,authorization_start='2030-01-01 18:00:00',authorization_end='2030-01-01 20:00:00')
  with self.assertRaises(ValueError):auto._exception_input(doc,'Correct Worked Hours','Reason',[{'start':doc.authorization_start,'end':doc.authorization_end}])
if __name__=='__main__':unittest.main()
