"""Native controller branches with the site-free adapter; no production data."""
import hashlib
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

adapter = runpy.run_path(str(Path(__file__).with_name('test_manual_overtime.py')), run_name='history_adapter')
from powerpro.controllers import retroactive_documentation as h
from powerpro.controllers import overtime_cash_settlement as cash
from powerpro.power_pro.doctype.retroactive_overtime_adjustment.retroactive_overtime_adjustment import RetroactiveOvertimeAdjustment as Controller
R = adapter['Record']

class Doc(Controller):
    def set(self, key, value): self[key] = value

class HistoryTest(unittest.TestCase):
    def setUp(self):
        self.doc = Doc(doctype=h.DT, name='HIST', employee='EMP', company='IGC', docstatus=0,
            work_date='2026-08-16', authorization_start='2026-08-16 18:00:00', authorization_end='2026-08-17 06:00:00',
            maximum_hours=11, historical_documentation=1, historical_disposition='Already Paid',
            historical_reference='PDF page 7; operator confirms previously paid. Break time estimated.',
            historical_source_file='/private/files/evidence.pdf', historical_break_start='2026-08-16 21:00:00',
            historical_break_end='2026-08-16 22:00:00', historical_break_estimated=1,
            historical_acknowledged=1, settlement_payroll_date='2026-08-30',
            approver=h.frappe.session.user, planned_settlement='Cash')
        self.file = R(name='FILE', file_url=self.doc.historical_source_file, get_content=lambda:b'PDF evidence')

    def submit(self):
        with patch.object(h.frappe.db, 'exists', return_value=False), \
             patch.object(h.frappe, 'get_all', return_value=['FILE']), \
             patch.object(h.frappe, 'get_doc', return_value=self.file):
            h.submit(self.doc)

    def test_overnight_one_hour_break_documented_not_payable(self):
        h.validate(self.doc); self.submit()
        self.assertEqual(self.doc.historical_hours, 11)
        self.assertEqual(self.doc.status, 'Documented')
        self.assertEqual(self.doc.settlement_status, 'Not Applicable')
        self.assertEqual(self.doc.verified_hours, 0)
        self.assertEqual(self.doc.settlement_amount, 0)
        self.assertIsNone(self.doc.evidence_snapshot)
        snap=json.loads(self.doc.historical_snapshot)
        self.assertEqual(snap['sha256'], hashlib.sha256(b'PDF evidence').hexdigest())
        self.assertTrue(snap['break_is_estimate'])
        self.assertEqual(snap['recorded_by'],h.frappe.session.user)
        self.assertEqual(len(snap['declared_intervals']),2)

    def test_ordinary_morning_can_document_zero_overtime(self):
        self.doc.update(authorization_start='2026-08-14 08:00:00', authorization_end='2026-08-14 09:45:00',
            maximum_hours=1.75, historical_break_start=None, historical_break_end=None,
            historical_disposition='Ordinary Work')
        h.validate(self.doc); self.submit()
        self.assertEqual(self.doc.historical_hours,1.75)
        self.assertEqual(self.doc.verified_hours,0)

    def test_break_bounds_and_incomplete_break(self):
        for start,end in [('2026-08-16 17:00','2026-08-16 18:00'),('2026-08-16 22:00','2026-08-16 21:00'),('2026-08-16 21:00',None)]:
            with self.subTest(start=start,end=end):
                self.doc.historical_break_start=start; self.doc.historical_break_end=end
                with self.assertRaises(ValueError):h.recorded_intervals(self.doc)

    def test_cannot_hide_hours_with_cap_or_remove_entire_window(self):
        self.doc.maximum_hours=10
        with self.assertRaises(ValueError):h.recorded_intervals(self.doc)
        self.doc.maximum_hours=12
        self.doc.historical_break_start=self.doc.authorization_start
        self.doc.historical_break_end=self.doc.authorization_end
        with self.assertRaises(ValueError):h.recorded_intervals(self.doc)

    def test_existing_salary_election_or_credit_blocks_conversion(self):
        for target in ['Additional Salary','Overtime Settlement Election','Overtime Compensatory Credit']:
            with self.subTest(target=target), patch.object(h.frappe.db,'exists',side_effect=lambda dt,f:dt==target):
                with self.assertRaisesRegex(ValueError,'vigente'):h.submit(self.doc)
                with self.assertRaisesRegex(ValueError,'vigente'):h.validate(self.doc)

    def test_confirmation_and_attached_readable_source_required(self):
        self.doc.historical_acknowledged=0
        with self.assertRaises(ValueError):self.submit()
        self.doc.historical_acknowledged=1
        with patch.object(h.frappe.db,'exists',return_value=False),patch.object(h.frappe,'get_all',return_value=[]):
            with self.assertRaisesRegex(ValueError,'Adjunte'):h.submit(self.doc)
        self.file.denied=['read']
        with self.assertRaises(PermissionError):self.submit()

    def test_native_submit_preserves_assigned_approver_and_skips_financial_engine(self):
        h.validate(self.doc)
        with patch.object(Controller,'_validate_feature_flag'),patch.object(Controller,'_validate_window'), \
             patch('powerpro.controllers.retroactive_evidence.reconcile',side_effect=AssertionError('Must not recalculate payment')), \
             patch.object(h,'submit') as close:
            self.doc.before_submit(); close.assert_called_once_with(self.doc)
            close.reset_mock(); self.doc.approver='someone-else'
            with self.assertRaises(PermissionError):self.doc.before_submit()
            close.assert_not_called()

    def test_cash_service_and_manual_salary_link_rejected(self):
        with self.assertRaisesRegex(ValueError,'otra liquidación'):cash.build_cash_settlement(self.doc,{})
        with self.assertRaises(ValueError):cash._create_additional_salaries(self.doc,{})
        salary=R(ref_doctype=h.DT,ref_docname='HIST')
        with patch.object(h.frappe,'get_doc',return_value=self.doc):
            with self.assertRaises(ValueError):h.prevent_salary_link(salary)
        h.prevent_salary_link(R(ref_doctype='Employee Advance',ref_docname='ADV'))

    def test_submitted_mode_cannot_be_toggled_or_changed(self):
        self.doc.before=R(docstatus=1,doctype=h.DT,historical_documentation=1)
        self.doc.historical_documentation=0
        with self.assertRaises(ValueError):h.validate(self.doc)
        with self.assertRaises(ValueError):self.doc.before_update_after_submit()
        self.doc.historical_documentation=1
        with self.assertRaises(ValueError):h.validate(self.doc)

    def test_reference_required_and_client_audit_is_overwritten(self):
        self.doc.historical_reference=''
        with self.assertRaises(ValueError):h.validate(self.doc)
        self.doc.historical_reference='Documented by operator'
        self.doc.update(historical_snapshot='forged',verified_hours=99,approved_by='fake',settlement_amount=9999)
        h.validate(self.doc)
        self.assertIsNone(self.doc.historical_snapshot)
        self.assertIsNone(self.doc.approved_by)
        self.assertEqual(self.doc.verified_hours,0)
        self.assertEqual(self.doc.settlement_amount,0)

    def test_existing_normal_adjustments_not_converted(self):
        self.doc.historical_documentation=0
        self.doc.reconciliation_engine='Verified Checkins'
        self.doc.verified_hours=5;self.doc.settlement_status='Created'
        h.validate(self.doc);h.reject_settlement(self.doc)
        self.assertEqual(self.doc.verified_hours,5)
        self.assertEqual(self.doc.settlement_status,'Created')
        self.doc.reconciliation_engine='Documentary'
        with self.assertRaises(ValueError):h.validate(self.doc)

    def test_cancel_keeps_historical_snapshot_without_reversing_money(self):
        h.validate(self.doc);self.submit()
        snap=self.doc.historical_snapshot
        with patch.object(Doc,'db_set') as save:
            self.doc.on_cancel()
            save.assert_called_once_with('status','Cancelled',update_modified=False)
        self.assertEqual(self.doc.historical_snapshot,snap)

if __name__=='__main__':unittest.main()
