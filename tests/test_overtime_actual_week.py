"""Actual weekly bands and completeness; never assume 44 ordinary hours."""
import copy
import unittest
from test_overtime_calendar import context,dt,legacy,rules
from powerpro.payroll_rules.overtime_actual_week import collect_weekly_work,apply_actual_week_bands,weekly_bands_ready
from powerpro.payroll_rules.overtime_shift_evidence import ALTERNATING,EVERY_PAIR


def punch(clock,kind='IN',day='2026-09-21'):
    return {'name':day+clock+kind,'time':day+'T'+clock,'log_type':kind,'shift':'DAY',
            'shift_start':day+'T08:00','shift_end':day+'T18:00'}


class WeeklyEvidenceTest(unittest.TestCase):
    def args(self):
        schedule=context('2026-09-21');schedule['shift']='DAY'
        return dict(start='2026-09-21T00:00',cutoff='2026-09-21T20:00',
                    rows=[punch('08:00'),punch('12:00','OUT'),punch('13:00'),punch('20:00','OUT')],
                    policies={'DAY':{'last_sync_of_checkin':'2026-09-22T00:00',
                        'determine_check_in_and_check_out':ALTERNATING,'working_hours_calculation_based_on':EVERY_PAIR}},
                    schedules=[schedule],attendances=[])
    def test_complete_monday_has_eleven_hours_not_forty_four(self):
        result=collect_weekly_work(**self.args())
        self.assertTrue(result['complete'])
        self.assertEqual(sum((dt(r['end'])-dt(r['start'])).total_seconds()/3600 for r in result['intervals']),11)
    def test_missing_day_requires_review_not_zero(self):
        a=self.args();a['rows']=[]
        r=collect_weekly_work(**a)
        self.assertFalse(r['complete']);self.assertIn('weekly_day_without_evidence',[i['code'] for i in r['issues']])
    def test_submitted_absence_covers_day_but_present_does_not_invent_hours(self):
        a=self.args();a['rows']=[]
        for status,expected in [('Absent',True),('On Leave',True),('Present',False)]:
            a['attendances']=[{'name':'ATT','attendance_date':'2026-09-21','status':status,'docstatus':1}]
            self.assertEqual(collect_weekly_work(**a)['complete'],expected)
    def test_draft_absence_cannot_cover_day(self):
        a=self.args();a['rows']=[];a['attendances']=[{'name':'ATT','attendance_date':'2026-09-21','status':'Absent','docstatus':0}]
        self.assertFalse(collect_weekly_work(**a)['complete'])
    def test_leave_conflicting_with_punches_requires_review(self):
        a=self.args();a['attendances']=[{'name':'ATT','attendance_date':'2026-09-21','status':'On Leave','docstatus':1}]
        self.assertIn('attendance_conflicts_with_checkins',[i['code'] for i in collect_weekly_work(**a)['issues']])
    def test_scheduled_holiday_without_punches_is_not_missing_ordinary_day(self):
        a=self.args();a['rows']=[];a['schedules'][0]['classification']=legacy.LEGAL_HOLIDAY
        self.assertTrue(collect_weekly_work(**a)['complete'])
    def test_unsynced_week_does_not_certify(self):
        a=self.args();a['policies']['DAY']['last_sync_of_checkin']=None
        self.assertFalse(collect_weekly_work(**a)['complete'])
    def test_skipped_and_offshift_evidence_are_not_silently_omitted(self):
        for flag in ['skip_auto_attendance','offshift']:
            a=self.args();a['rows'][0][flag]=1
            self.assertFalse(collect_weekly_work(**a)['complete'])
    def test_current_extended_session_replaces_its_checkins_once(self):
        a=self.args();a['rows'][-1]['offshift']=1
        a['accepted_checkins']=[r['name'] for r in a['rows']]
        a['accepted_intervals']=[{'start':'2026-09-21T08:00','end':'2026-09-21T12:00'},
                                 {'start':'2026-09-21T13:00','end':'2026-09-21T20:00'}]
        r=collect_weekly_work(**a);self.assertTrue(r['complete']);self.assertEqual(len(r['intervals']),2)
    def test_duplicate_or_overlapping_sessions_require_review(self):
        a=self.args();a['rows'].append(copy.deepcopy(a['rows'][0]))
        self.assertFalse(collect_weekly_work(**a)['complete'])
        a=self.args();a['accepted_intervals']=[{'start':'2026-09-21T09:00','end':'2026-09-21T10:00'}]
        self.assertFalse(collect_weekly_work(**a)['complete'])
    def test_unknown_schedule_and_calendar_fail_closed(self):
        a=self.args();a['context_issues']=[{'code':'weekly_shift_ambiguous'}]
        self.assertFalse(collect_weekly_work(**a)['complete'])
        a=self.args();a['schedules'][0]['holiday_list_covers_work_date']=False
        self.assertFalse(collect_weekly_work(**a)['complete'])


class ActualBandsTest(unittest.TestCase):
    def calc(self,start='2026-09-25T18:00',end='2026-09-25T20:00',contexts=None):
        return rules.reconcile_calendar_intervals(authorization_start=start,authorization_end=end,maximum_hours=5,
            intervals=[legacy.WorkInterval(dt(start),dt(end))],contexts=contexts or [context('2026-09-25')])
    def week(self,prior=0):
        # Five disjoint worked days; the fifth ordinary block ends at OT start.
        rows=[]
        from datetime import timedelta
        for day in range(21,25):
            hours=min(prior,16);prior-=hours
            if hours:rows.append({'start':f'2026-09-{day}T00:00','end':(dt(f'2026-09-{day}T00:00')+timedelta(hours=hours)).isoformat()})
        if prior:rows.append({'start':(dt('2026-09-25T18:00')-timedelta(hours=prior)).isoformat(),'end':'2026-09-25T18:00'})
        rows.append({'start':'2026-09-25T18:00','end':'2026-09-25T20:00'})
        return {'complete':True,'intervals':rows}
    def test_actual_threshold_crosses_inside_segment(self):
        r=apply_actual_week_bands(self.calc(),self.week(67.5),threshold=68)
        self.assertEqual((r['regular_35_hours'],r['regular_100_hours']),(.5,1.5))
    def test_missing_ordinary_days_do_not_assume_forty_four_hours(self):
        r=apply_actual_week_bands(self.calc(),self.week(20),threshold=68)
        self.assertEqual((r['regular_35_hours'],r['regular_100_hours']),(2,0))
        w=self.week(20);w['complete']=False
        r=apply_actual_week_bands(self.calc(),w,threshold=68)
        self.assertEqual((r['verified_hours'],r['regular_35_hours'],r['regular_100_hours'],r['unclassified_regular_hours']),(2,0,0,2))
    def test_exact_threshold_and_one_second(self):
        r=apply_actual_week_bands(self.calc(),self.week(68),threshold=68)
        self.assertEqual(r['regular_100_hours'],2)
        r=apply_actual_week_bands(self.calc(),self.week(68-1/3600),threshold=68)
        self.assertEqual(r['regular_35_hours'],.0003)
    def test_sunday_monday_reset_uses_calendar_week(self):
        c=self.calc('2026-09-27T23:00','2026-09-28T02:00',[context('2026-09-27'),context('2026-09-28')])
        w=self.week(68);w['intervals'].append({'start':'2026-09-27T23:00','end':'2026-09-28T02:00'})
        r=apply_actual_week_bands(c,w,threshold=68)
        self.assertEqual((r['regular_35_hours'],r['regular_100_hours']),(2,1))
    def test_holiday_hours_stay_separate_while_contributing_to_actual_week(self):
        c=self.calc(contexts=[context('2026-09-25',legacy.LEGAL_HOLIDAY)])
        r=apply_actual_week_bands(c,self.week(68),threshold=68)
        self.assertEqual((r['holiday_100_hours'],r['regular_100_hours']),(2,0))
    def test_incomplete_interval_coverage_does_not_certify_a_segment(self):
        w=self.week();w['intervals']=[]
        r=apply_actual_week_bands(self.calc(),w,threshold=68)
        self.assertFalse(r['weekly_evidence_complete']);self.assertEqual(r['unclassified_regular_hours'],2)
    def test_duplicate_intervals_are_not_double_counted(self):
        w=self.week(40);w['intervals']+=copy.deepcopy(w['intervals'])
        r=apply_actual_week_bands(self.calc(),w,threshold=68)
        self.assertEqual(r['segments'][0]['actual_weekly_hours_before'],40)
    def test_calculation_is_not_mutated_and_bad_thresholds_rejected(self):
        c=self.calc();before=copy.deepcopy(c)
        apply_actual_week_bands(c,self.week(68),threshold=68);self.assertEqual(c,before)
        for threshold in [0,-1,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):apply_actual_week_bands(c,self.week(),threshold=threshold)


class WeeklyBandReadinessTest(unittest.TestCase):
    def calc(self, classification=legacy.WEEKLY_REST):
        return {'weekly_evidence_complete':False,'verified_hours':5,
                'regular_35_hours':0,'regular_100_hours':0,'unclassified_regular_hours':0,
                'segments':[{'classification':classification,'verified_hours':5}]}

    def test_independent_day_does_not_certify_the_week(self):
        for kind in (legacy.WEEKLY_REST,legacy.LEGAL_HOLIDAY,legacy.HOLIDAY_ON_WEEKLY_REST):
            c=self.calc(kind); before=copy.deepcopy(c)
            self.assertTrue(weekly_bands_ready(c)); self.assertEqual(c,before)
            self.assertFalse(c['weekly_evidence_complete'])

    def test_regular_and_mixed_windows_still_require_week(self):
        c=self.calc(legacy.REGULAR_DAY)
        self.assertFalse(weekly_bands_ready(c))
        c=self.calc();c['segments'].append({'classification':legacy.REGULAR_DAY,'verified_hours':1});c['verified_hours']=6
        self.assertFalse(weekly_bands_ready(c))

    def test_unclassified_or_unknown_hours_fail_closed(self):
        for key in ('regular_35_hours','regular_100_hours','unclassified_regular_hours'):
            c=self.calc();c[key]=1;self.assertFalse(weekly_bands_ready(c))
        self.assertFalse(weekly_bands_ready(self.calc('Unknown')))
        for c in (None,{}, {'weekly_evidence_complete':False,'segments':[]}):
            self.assertFalse(weekly_bands_ready(c))

    def test_inconsistent_zero_or_nonfinite_totals_fail_closed(self):
        for value in (0,-1,6,float('nan'),float('inf')):
            c=self.calc();c['verified_hours']=value;self.assertFalse(weekly_bands_ready(c))
        for value in (0,-1,float('nan'),float('inf')):
            c=self.calc();c['segments'][0]['verified_hours']=value;self.assertFalse(weekly_bands_ready(c))

    def test_complete_week_preserves_regular_readiness(self):
        c=self.calc(legacy.REGULAR_DAY);c['weekly_evidence_complete']=True
        self.assertTrue(weekly_bands_ready(c))


if __name__=='__main__':unittest.main()
