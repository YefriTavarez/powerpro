"""A later adjustment must reuse the reviewed observation window of prior work."""
from copy import deepcopy
from datetime import datetime
from contextlib import ExitStack
import json
import unittest
from unittest.mock import patch
import frappe
from powerpro.controllers import checkin_overtime_week as weekly
from powerpro.controllers import checkin_overtime as engine
from powerpro.payroll_rules.overtime_manual_session import evaluate_manual_session


class WeeklyScopedReviewTest(unittest.TestCase):
    def setUp(self):
        self.context=dict(date='2026-08-14',shift_start='2026-08-14 08:00:00',shift_end='2026-08-14 17:00:00',
                          classification='Regular Workday',holiday_list_covers_work_date=True)
        self.declaration=dict(full_session=True,reference='Reviewed historical session',review_scope='Authorized interval only',
            observation_window=dict(start='2026-08-14 07:40:15',end='2026-08-14 18:27:00'),
            intervals=[dict(start='2026-08-14 07:40:15',end='2026-08-14 13:04:56'),
                       dict(start='2026-08-14 13:56:15',end='2026-08-14 18:27:00')])
        self.current=dict(authorization=dict(name='PREVIOUS',start='2026-08-14 17:00:00',end='2026-08-14 18:00:00',maximum_hours=1,shift='D'),
            rows=[dict(name='P1',time='2026-08-14 07:40:15',log_type='IN'),dict(name='P2',time='2026-08-14 18:27:00',log_type='OUT')],
            shift=dict(name='D'),contexts=[self.context],next_windows=[],competing=False)
        self.prior=frappe._dict(name='PREVIOUS',doctype='Retroactive Overtime Adjustment',docstatus=1,
            authorization_start='2026-08-14 17:00:00',authorization_end='2026-08-14 18:00:00',reconciliation_source='Manual Verification')
        self.doc=frappe._dict(name='LATER',doctype='Retroactive Overtime Adjustment',employee='TEST',
            authorization_start='2026-08-16 08:00:00',authorization_end='2026-08-16 16:30:00')
        self.freeze()

    def freeze(self):
        saved=evaluate_manual_session(declaration=self.declaration,authorization=self.current['authorization'],rows=self.current['rows'],
            contexts=self.current['contexts'],now=datetime(2026,9,14),observation_window=self.declaration.get('observation_window'))
        saved['review']={'manual_declaration':deepcopy(self.declaration)}
        saved['input']=deepcopy(self.current)
        self.saved=saved
        self.prior.evidence_snapshot=json.dumps(saved,default=str)

    def load(self):
        def records(dt,**kwargs):
            return [self.prior] if dt=='Retroactive Overtime Adjustment' else []
        def get_doc(dt,name,**kwargs):
            if dt=='Company':return frappe._dict(default_holiday_list='H')
            if dt=='Shift Type':return frappe._dict(name='D',holiday_list='H')
            return self.prior
        def data(doc,**kwargs):
            current=deepcopy(self.current)
            if kwargs.get('observation_window'):current['observation_window']=kwargs['observation_window']
            return current,frappe._dict()
        with ExitStack() as stack:
            stack.enter_context(patch.object(weekly,'_reconciliation_rows',side_effect=records))
            stack.enter_context(patch.object(frappe,'get_doc',side_effect=get_doc))
            stack.enter_context(patch.object(weekly,'get_schedule_context',return_value=deepcopy(self.context)))
            mock_data=stack.enter_context(patch.object(engine,'_data',side_effect=data))
            stack.enter_context(patch.object(engine,'now_datetime',return_value=datetime(2026,9,14)))
            mock_clock=stack.enter_context(patch('powerpro.payroll_rules.overtime_evidence.evaluate_evidence',return_value={}))
            result=weekly.load_week(self.doc,frappe._dict(company='C',default_shift='D'),[],for_update=True)
            return result,mock_data.call_args.kwargs,mock_clock.call_args.kwargs

    def test_later_day_preserves_complete_prior_scoped_session(self):
        result,data,clock=self.load()
        self.assertEqual(result['historical_intervals'],self.saved['worked_intervals'])
        self.assertEqual(result['historical_checkins'],['P1','P2'])
        self.assertEqual(result['context_issues'],[])
        self.assertEqual(len(result['certified_sessions']),1)
        self.assertEqual(data['observation_window'],self.declaration['observation_window'])
        self.assertEqual(clock['observation_window'],self.declaration['observation_window'])
        self.assertTrue(data['scoped_manual_review'])
        self.assertTrue(data['for_update'])
        self.assertFalse(data['include_weekly'])

    def test_legacy_session_does_not_gain_expanded_window(self):
        self.declaration.pop('review_scope');self.declaration.pop('observation_window')
        self.declaration['intervals']=[dict(start='2026-08-14 08:00:00',end='2026-08-14 18:00:00')]
        self.freeze()
        result,data,clock=self.load()
        self.assertEqual(result['context_issues'],[])
        self.assertIsNone(data['observation_window'])
        self.assertIsNone(clock['observation_window'])
        self.assertFalse(data['scoped_manual_review'])

    def test_unscoped_out_of_bounds_declaration_still_fails(self):
        self.declaration.pop('review_scope')
        self.freeze()
        with self.assertRaises(ValueError):self.load()

    def test_changed_original_punch_is_not_silently_accepted(self):
        self.current['rows'][0]['time']='2026-08-14 07:45:00'
        result,_,_=self.load()
        self.assertEqual(result['historical_intervals'],[])
        self.assertEqual(result['context_issues'][0]['code'],'weekly_previous_snapshot_changed')

    def test_invalid_scoped_reference_is_not_accepted(self):
        self.declaration['reference']=''
        self.saved['review']['manual_declaration']=self.declaration
        self.prior.evidence_snapshot=json.dumps(self.saved,default=str)
        with self.assertRaises(ValueError):self.load()
