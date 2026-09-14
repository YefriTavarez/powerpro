"""Historical interval approval keeps physical work and settlement guards."""
from copy import deepcopy
from datetime import datetime
import unittest
from unittest.mock import patch
import frappe
from powerpro.controllers import checkin_overtime as engine
from powerpro.controllers.checkin_overtime_review import accept_result
from powerpro.payroll_rules.overtime_manual_session import authorized_interval_scope


class RetroactiveIntervalReviewTest(unittest.TestCase):
    def setUp(self):
        self.doc=frappe._dict(doctype='Retroactive Overtime Adjustment',name='TEST',docstatus=0,
            planned_settlement='Cash',evidence_snapshot=None)
        self.declaration=dict(full_session=True,reference='Signed historical interval and complete clock pairs',
            review_scope='Authorized interval only',
            observation_window=dict(start='2026-08-14 07:40:15',end='2026-08-14 18:27:00'),
            intervals=[dict(start='2026-08-14 07:40:15',end='2026-08-14 13:04:56'),
                       dict(start='2026-08-14 13:56:15',end='2026-08-14 18:27:00')])
        context=dict(date='2026-08-14',shift_start='2026-08-14 08:00:00',shift_end='2026-08-14 17:00:00',
            classification='Regular Workday',holiday_list_covers_work_date=True)
        self.data=dict(authorization=dict(name='TEST',start='2026-08-14 17:00:00',end='2026-08-14 18:00:00',maximum_hours=1,shift='D'),
            contexts=[context],rows=[],next_windows=[],competing=False,
            shift=dict(name='D',determine_check_in_and_check_out='Strictly based on Log Type in Employee Checkin'),
            pay_policy=dict(weekly_threshold=68,night_basis='Clock overlap',holiday_weekly_rest_mode='Require review'),
            rate_basis=dict(hourly_rate=100),observation_window=self.declaration['observation_window'],
            weekly=dict(start='2026-08-10 00:00:00',cutoff='2026-08-14 18:00:00',rows=[],policies={},attendances=[],
                schedules=[dict(context,date='2026-08-13',shift='D',shift_start='2026-08-13 08:00:00',shift_end='2026-08-13 18:00:00'),dict(context,shift='D')]))
        # Source records are kept exactly as supplied; the manual route does not
        # require manufacturing punches when documenting a historical session.
        self.data['rows']=[dict(name='P1',time='2026-08-14 07:40:15',log_type='IN'),dict(name='P2',time='2026-08-14 18:27:00',log_type='OUT')]

    def build(self,declaration=None):
        with patch.object(engine,'_data',return_value=(deepcopy(self.data),frappe._dict())), \
             patch.object(engine,'now_datetime',return_value=datetime(2026,9,14)), \
             patch('powerpro.controllers.overtime_rest.get_election',return_value=None):
            return engine.build_result(self.doc,manual_declaration=declaration or self.declaration)

    def accept(self,result):
        return accept_result(result,dict(input_hash=result['input_hash'],reason='Approve only the requested hour'))

    def test_approve_one_hour_preserving_physical_session_and_pending_week(self):
        result=self.build();accepted=self.accept(result)
        self.assertEqual(accepted['state'],'Verified')
        self.assertEqual(accepted['snapshot']['verified_hours'],1)
        self.assertEqual(accepted['snapshot']['actual_start'],datetime(2026,8,14,17))
        self.assertEqual(accepted['snapshot']['actual_end'],datetime(2026,8,14,18))
        self.assertEqual(accepted['source_checkins'],self.data['rows'])
        self.assertEqual(accepted['worked_intervals'][0]['start'],'2026-08-14T07:40:15')
        self.assertEqual(accepted['worked_intervals'][-1]['end'],'2026-08-14T18:27:00')
        self.assertAlmostEqual(accepted['calculation']['unapproved_hours'],.45,places=4)
        self.assertFalse(accepted['settlement_ready'])
        self.assertFalse(accepted['weekly_evidence']['complete'])
        self.assertTrue(any('semanal' in x for x in accepted['settlement_blockers']))
        self.assertEqual(accepted['calculation']['regular_35_hours'],0)
        self.assertEqual(accepted['calculation']['regular_100_hours'],0)

    def test_existing_unapproved_time_guard_is_unchanged_without_explicit_scope(self):
        result=self.build();result.pop('authorized_interval_review')
        with patch('frappe.throw',side_effect=frappe.ValidationError):
            with self.assertRaises(frappe.ValidationError):self.accept(result)

    def test_missing_or_ambiguous_evidence_cannot_be_accepted(self):
        for code in ('missing_punch_pair','overlapping_authorization','next_shift_overlap'):
            result=self.build();result['issues'].append(dict(code=code,severity='review'))
            with patch('frappe.throw',side_effect=frappe.ValidationError):
                with self.assertRaises(frappe.ValidationError):self.accept(result)

    def test_only_explicit_complete_historical_declaration_can_opt_in(self):
        self.assertFalse(authorized_interval_scope(None,self.doc.doctype))
        for source,change in [('Overtime Authorization',{}),(self.doc.doctype,{'full_session':False}),
            (self.doc.doctype,{'reference':''}),(self.doc.doctype,{'observation_window':None}),
            (self.doc.doctype,{'review_scope':'anything'})]:
            with self.assertRaises(ValueError):authorized_interval_scope({**self.declaration,**change},source)

    def test_cannot_hide_work_by_shrinking_observation_window(self):
        declaration={**self.declaration,'observation_window':dict(start='2026-08-14 17:00:00',end='2026-08-14 18:00:00')}
        self.data['observation_window']=declaration['observation_window']
        with self.assertRaises(ValueError):self.build(declaration)

    def test_saved_review_rebuilds_with_same_scope(self):
        result=self.build();accepted=self.accept(result)
        accepted['review']['manual_declaration']=self.declaration
        self.doc.evidence_snapshot=engine._json(accepted)
        with patch.object(engine,'_data',return_value=(deepcopy(self.data),frappe._dict())), \
             patch.object(engine,'now_datetime',return_value=datetime(2026,9,14)), \
             patch('powerpro.controllers.overtime_rest.get_election',return_value=None):
            rebuilt=engine.build_result(self.doc)
        self.assertEqual(rebuilt['state'],'Verified')
        self.assertEqual(rebuilt['input_hash'],accepted['input_hash'])
        self.assertFalse(rebuilt['settlement_ready'])
