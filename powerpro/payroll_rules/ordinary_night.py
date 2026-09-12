"""Ordinary night premium from a complete evidenced shift, without an OT document."""
from copy import deepcopy
from datetime import timedelta
from powerpro.payroll_rules.overtime import _as_datetime, WorkInterval, _subtract_interval
from powerpro.payroll_rules.overtime_shift_evidence import interpret_shift_punches, union_intervals
from powerpro.payroll_rules.overtime_pay_policy import classify_night_session

VERSION = 'ordinary-night-v1'


def evaluate_night_work(*, rows, shift, context, extensions, next_windows, now, basis):
    start, end = _as_datetime(context['shift_start']), _as_datetime(context['shift_end'])
    windows = [(start, end)] + [(_as_datetime(r['start']), _as_datetime(r['end'])) for r in extensions]
    if any(b <= a for a, b in windows):
        raise ValueError('Ventana de trabajo inválida.')
    lo, hi = min(a for a, b in windows), max(b for a, b in windows)
    before = timedelta(minutes=float(shift.get('begin_check_in_before_shift_start_time') or 0))
    after = timedelta(minutes=float(shift.get('allow_check_out_after_shift_end_time') or 0))
    result = {'version': VERSION, 'state': 'Verified', 'issues': [], 'source_checkins': [], 'interpretations': []}
    def issue(code, severity='review'):
        if not any(r['code'] == code for r in result['issues']):
            result['issues'].append({'code': code, 'severity': severity})
    if not context.get('holiday_list_covers_work_date'): issue('calendar_incomplete')
    if context['classification'] != 'Regular Workday': issue('not_an_ordinary_workday')
    if hi - lo > timedelta(hours=24): issue('extended_session_over_24h')
    if _as_datetime(now) < hi + after: issue('window_not_ended', 'wait')
    if not shift.get('last_sync_of_checkin') or _as_datetime(shift['last_sync_of_checkin']) < hi + after:
        issue('sync_incomplete', 'wait')
    if any(b[0] < a[1] for a, b in zip(sorted(windows[1:]), sorted(windows[1:])[1:])):
        issue('overlapping_authorization')
    grouped = []
    for raw in rows:
        stamp = _as_datetime(raw['time'])
        if not lo - before <= stamp <= hi + after: continue
        result['source_checkins'].append(deepcopy(raw))
        captured = (raw.get('shift') == shift['name'] and raw.get('shift_start') and raw.get('shift_end')
                    and _as_datetime(raw['shift_start']) == start and _as_datetime(raw['shift_end']) == end)
        if raw.get('skip_auto_attendance'): issue('excluded_checkin'); continue
        if any(_as_datetime(w['start']) <= stamp <= _as_datetime(w['end']) for w in next_windows):
            issue('next_shift_overlap'); continue
        if not captured and not any(a <= stamp <= b + after for a, b in windows[1:]):
            issue('checkin_without_matching_shift'); continue
        row = deepcopy(raw)
        row.update(shift=shift['name'], shift_start=lo, shift_end=hi,
                   shift_actual_start=lo-before, shift_actual_end=hi+after, offshift=0)
        if not captured:
            result['interpretations'].append({'checkin': raw.get('name'), 'reason': 'approved_extension',
                                              'stored_log_type': raw.get('log_type')})
        grouped.append(row)
    evidence = interpret_shift_punches(grouped, {shift['name']: shift})
    result['sessions'] = evidence['sessions']
    for warning in evidence['issues']:
        issue(warning['code'], 'information' if warning['code'] in {'direction_reinterpreted', 'first_last_includes_breaks'} else 'review')
    worked = evidence['intervals']
    if not worked: issue('missing_punch_pair')
    # Anything outside the documented ordinary shift and approved extensions is
    # retained for review, not paid as an ordinary hour by this document.
    outside = [WorkInterval(a, b) for a, b in worked]
    for a, b in union_intervals(windows): outside = _subtract_interval(outside, WorkInterval(a, b))
    result['unapproved_intervals'] = [{'start': r.start.isoformat(), 'end': r.end.isoformat()} for r in outside]
    if outside: issue('work_outside_documented_window')
    as_rows = lambda pairs: [{'start': a.isoformat(), 'end': b.isoformat()} for a, b in pairs]
    ordinary = [(max(a, start), min(b, end)) for a, b in worked if max(a, start) < min(b, end)]
    extra = [WorkInterval(a, b) for a, b in worked]
    extra = _subtract_interval(extra, WorkInterval(start, end))
    result['worked_intervals'] = as_rows(worked)
    result['ordinary_intervals'] = as_rows(ordinary)
    result['overtime_intervals'] = [{'start': r.start.isoformat(), 'end': r.end.isoformat()} for r in extra]
    if worked:
        result['night_session'] = classify_night_session(result['worked_intervals'], result['overtime_intervals'], basis=basis)
    if any(r['severity'] != 'information' for r in result['issues']):
        result['state'] = 'Waiting' if any(r['severity'] == 'wait' for r in result['issues']) else 'Needs Review'
    return result
