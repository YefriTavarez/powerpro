"""Actual weekly evidence and chronological bands, without presumed ordinary hours.

Completeness describes the supplied evidence and schedule, not approval of the
payroll policy. All worked intervals count toward the supplied weekly threshold;
holiday/rest remuneration remains separately classified by the calendar engine.
"""
from copy import deepcopy
from datetime import datetime, time, timedelta
from math import isfinite

from powerpro.payroll_rules.overtime import REGULAR_DAY, _as_datetime
from powerpro.payroll_rules.overtime_shift_evidence import interpret_shift_punches, union_intervals, captured_window_kind

INFORMATIONAL = {'direction_reinterpreted', 'first_last_includes_breaks'}


def collect_weekly_work(*, start, cutoff, rows, policies, schedules, attendances,
                        accepted_intervals=(), accepted_checkins=(), context_issues=(), certified_sessions=()):
    """Require evidence for every elapsed ordinary shift in the supplied schedule.

The caller supplies schedules from the day before the first week (overnight
carry) through cutoff. Absence/leave proves zero only without conflicting
punches. An accepted current authorization supplies its complete worked session,
including ordinary time, while keeping original Checkins as dependencies.
    """
    start, cutoff = _as_datetime(start), _as_datetime(cutoff)
    if start.weekday() or start.time() != time.min or cutoff <= start:
        raise ValueError('Ventana semanal inválida.')
    if cutoff - start > timedelta(days=9):
        raise ValueError('La evidencia semanal supera el límite de nueve días.')
    relevant = [r for r in rows if _as_datetime(r['time']) <= cutoff]
    accepted_names = set(accepted_checkins)
    remaining = [r for r in relevant if r.get('name') not in accepted_names]
    interpreted = interpret_shift_punches(remaining, policies)
    issues = [deepcopy(i) for i in context_issues]
    issues.extend(i for i in interpreted['issues'] if i['code'] not in INFORMATIONAL)
    intervals = list(interpreted['intervals'])
    intervals.extend((_as_datetime(r['start']), _as_datetime(r['end'])) for r in accepted_intervals)
    if any(b <= a or b-a > timedelta(hours=24) for a,b in intervals):
        raise ValueError('Intervalo semanal inválido.')
    # Overlapping sources are counted once, but differing sessions require review.
    ordered = sorted(intervals)
    if any(a < previous_b for (_, previous_b), (a, _) in zip(ordered, ordered[1:])):
        issues.append({'code': 'overlapping_work_sessions'})
    worked = union_intervals(intervals)
    coverage = []
    for schedule in schedules:
        day = schedule['date']
        a,b = _as_datetime(schedule['shift_start']), _as_datetime(schedule['shift_end'])
        if b <= start or a >= cutoff:
            continue
        item = {'date': day, 'shift': schedule['shift'], 'state': 'covered'}
        local = []
        if not schedule.get('holiday_list_covers_work_date'):
            local.append('weekly_calendar_uncovered')
        policy = policies.get(schedule['shift']) or {}
        certified=any(r.get('shift')==schedule['shift'] and _as_datetime(r['start'])==a and _as_datetime(r['end'])==b for r in certified_sessions)
        synced = policy.get('last_sync_of_checkin')
        if not certified and (not synced or _as_datetime(synced) < min(b, cutoff)):
            local.append('weekly_sync_incomplete')
        matching = [r for r in relevant if captured_window_kind(r,schedule['shift'],a,b,policy)]
        valid = any(captured_window_kind(session,schedule['shift'],a,b,policy)
                    for session in interpreted['sessions'])
        accepted = any(r.get('name') in accepted_names for r in matching)
        absence = [r for r in attendances if str(r['attendance_date']) == day
                   and r.get('docstatus') == 1 and r.get('status') in {'Absent','On Leave'}]
        has_work = any(lo < min(b,cutoff) and hi > max(a,start) for lo,hi in worked)
        if absence and (matching or has_work):
            local.append('attendance_conflicts_with_checkins')
        if schedule['classification'] == REGULAR_DAY and not (valid or accepted or certified or absence):
            local.append('weekly_day_without_evidence')
        if local:
            item['state'] = 'review'
            issues.extend({'code': code, 'date': day, 'shift': schedule['shift']} for code in local)
        elif certified:
            item['state']='hr_certified_session'
        elif absence:
            item.update(state='documented_nonwork', attendances=[r['name'] for r in absence])
        elif schedule['classification'] != REGULAR_DAY and not matching:
            item['state'] = 'scheduled_nonwork'
        coverage.append(item)
    if not coverage:
        issues.append({'code': 'weekly_schedule_missing'})
    return {'version': 'actual-week-v1', 'start': start.isoformat(), 'cutoff': cutoff.isoformat(),
            'complete': not issues, 'issues': issues, 'coverage': coverage,
            'sessions': interpreted['sessions'],
            'intervals': [{'start': max(a,start).isoformat(), 'end': min(b,cutoff).isoformat()}
                          for a,b in worked if a < cutoff and b > start]}


def apply_actual_week_bands(calculation, weekly, *, threshold):
    """Replace legacy 24-extra-hour bands with actual chronological weekly hours.

Incomplete evidence leaves regular hours explicitly unclassified. It does not
reduce verified worked hours, and it cannot certify payment eligibility.
    """
    threshold = float(threshold)
    if not isfinite(threshold) or threshold <= 0:
        raise ValueError('El umbral semanal debe ser positivo y finito.')
    result = deepcopy(calculation)
    result.update(regular_35_hours=0.0, regular_100_hours=0.0, unclassified_regular_hours=0.0,
                  weekly_basis='actual_worked_intervals', weekly_evidence_complete=bool(weekly['complete']))
    intervals = union_intervals([(_as_datetime(r['start']), _as_datetime(r['end'])) for r in weekly['intervals']])
    for segment in result['segments']:
        if segment['classification'] != REGULAR_DAY:
            continue
        a,b = _as_datetime(segment['start']), _as_datetime(segment['end'])
        week = datetime.combine((a-timedelta(days=a.weekday())).date(), time.min)
        covered = sum(max((min(hi,b)-max(lo,a)).total_seconds(),0) for lo,hi in intervals)
        before = sum(max((min(hi,a)-max(lo,week)).total_seconds(),0) for lo,hi in intervals)/3600
        hours = (b-a).total_seconds()/3600
        segment.update(regular_35_hours=0.0, regular_100_hours=0.0,
                       actual_weekly_hours_before=round(before,4))
        if not weekly['complete'] or abs(covered-(b-a).total_seconds()) > .001:
            segment['weekly_band_status']='review'
            result['weekly_evidence_complete']=False
            result['unclassified_regular_hours']+=hours
            continue
        lower = min(hours,max(threshold-before,0))
        upper = hours-lower
        segment.update(regular_35_hours=round(lower,4), regular_100_hours=round(upper,4), weekly_band_status='verified_evidence')
        result['regular_35_hours']+=lower
        result['regular_100_hours']+=upper
    for key in ['regular_35_hours','regular_100_hours','unclassified_regular_hours']:
        result[key]=round(result[key],4)
    return result


def weekly_bands_ready(calculation):
    """Require complete weekly evidence only where it selects a regular band.

    Do not relabel an incomplete week as complete. Independently classified
    holiday/rest segments still require policy, evidence, election and base
    coverage validation in the caller. Unknown or mixed classifications fail
    closed, as do inconsistent hour totals.
    """
    if not calculation:
        return False
    if calculation.get('weekly_evidence_complete') is True:
        return True
    segments = calculation.get('segments') or []
    if not segments:
        return False
    from powerpro.payroll_rules.overtime import LEGAL_HOLIDAY, WEEKLY_REST, HOLIDAY_ON_WEEKLY_REST
    independent = {LEGAL_HOLIDAY, WEEKLY_REST, HOLIDAY_ON_WEEKLY_REST}
    if any(s.get('classification') not in independent for s in segments):
        return False
    try:
        ordinary = [float(calculation.get(k) or 0) for k in
                    ('regular_35_hours', 'regular_100_hours', 'unclassified_regular_hours')]
        hours = [float(s['verified_hours']) for s in segments]
        total = float(calculation['verified_hours'])
    except (KeyError, TypeError, ValueError):
        return False
    return (all(isfinite(v) and v == 0 for v in ordinary)
            and all(isfinite(v) and v > 0 for v in hours)
            and isfinite(total) and total > 0 and abs(sum(hours) - total) <= .0001)
