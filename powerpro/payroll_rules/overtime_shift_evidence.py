"""Preview intervals from captured shift sessions and scoped HR corrections.

No site access. Current Shift Type options are an interpretation, not an immutable
historical policy or a certification of attendance.
"""
from datetime import timedelta
from powerpro.payroll_rules.overtime import _as_datetime, get_shift_window
from powerpro.payroll_rules.overtime_weekly import reconstruct_week

ALTERNATING = 'Alternating entries as IN and OUT during the same shift'
STRICT = 'Strictly based on Log Type in Employee Checkin'
FIRST_LAST = 'First Check-in and Last Check-out'
EVERY_PAIR = 'Every Valid Check-in and Check-out'


def captured_window_kind(row, shift_name, start, end, policy):
    """Match a resolved schedule to raw HRMS capture without rewriting it.

    HRMS captures the base Shift Type end even when the payroll schedule has
    an explicit Friday end. Only that exact, configured base/special pair is
    accepted; arbitrary mismatches and another shift remain unmatched.
    """
    if row.get('shift') != shift_name or not row.get('shift_start') or not row.get('shift_end'):
        return None
    a, b = _as_datetime(start), _as_datetime(end)
    captured = (_as_datetime(row['shift_start']), _as_datetime(row['shift_end']))
    if captured == (a, b):
        return 'exact'
    friday = policy.get('custom_hora_salida_viernes')
    if a.weekday() != 4 or not friday or not policy.get('start_time') or not policy.get('end_time'):
        return None
    base = get_shift_window(a.date(), policy['start_time'], policy['end_time'])
    special = get_shift_window(a.date(), policy['start_time'], policy['end_time'], friday)
    if base != special and special == (a, b) and captured == base:
        return 'friday_base'
    return None


def union_intervals(intervals):
    result = []
    for a, b in sorted(intervals):
        if b <= a:
            raise ValueError('Intervalo de trabajo inválido.')
        if result and a <= result[-1][1]:
            result[-1] = (result[-1][0], max(b, result[-1][1]))
        else:
            result.append((a, b))
    return result


def interpret_shift_punches(checkins, policies):
    groups, issues, intervals, sessions = {}, [], [], []
    def issue(code, rows):
        issues.append({'code': code, 'checkins': [str(r.get('name') or '') for r in rows]})
    for row in sorted(checkins, key=lambda r: (_as_datetime(r['time']), str(r.get('name') or ''))):
        if row.get('skip_auto_attendance'):
            issue('skip_auto_attendance', [row]); continue
        if row.get('offshift'):
            issue('offshift', [row]); continue
        if not all(row.get(k) for k in ['shift', 'shift_start', 'shift_end']):
            issue('missing_shift_window', [row]); continue
        a, b = _as_datetime(row['shift_start']), _as_datetime(row['shift_end'])
        if b <= a or b - a > timedelta(hours=24):
            issue('invalid_shift_window', [row]); continue
        if row.get('shift_actual_start') and row.get('shift_actual_end'):
            if not _as_datetime(row['shift_actual_start']) <= _as_datetime(row['time']) <= _as_datetime(row['shift_actual_end']):
                issue('outside_captured_window', [row]); continue
        groups.setdefault((row['shift'], a, b), []).append(row)
    for (shift, a, b), rows in sorted(groups.items()):
        policy = policies.get(shift)
        if not policy:
            issue('unavailable_shift_policy', rows); continue
        mode, calc = policy.get('determine_check_in_and_check_out'), policy.get('working_hours_calculation_based_on')
        if mode not in {ALTERNATING, STRICT} or calc not in {FIRST_LAST, EVERY_PAIR}:
            issue('unsupported_shift_policy', rows); continue
        stamps = [_as_datetime(r['time']) for r in rows]
        if len(set(stamps)) != len(stamps):
            issue('duplicate_timestamp', rows); continue
        if len(rows) < 2:
            issue('insufficient_shift_punches', rows); continue
        chosen = []
        if mode == ALTERNATING:
            if len(rows) % 2:
                issue('odd_alternating_count', rows)
            if any(str(r.get('log_type') or '').upper() not in {'', 'IN' if i % 2 == 0 else 'OUT'} for i, r in enumerate(rows)):
                issue('direction_reinterpreted', rows)
            if calc == FIRST_LAST:
                chosen = [(stamps[0], stamps[-1])]
            else:
                chosen = list(zip(stamps[::2], stamps[1::2]))
        else:
            first, last, opened = None, None, None
            for row, stamp in zip(rows, stamps):
                kind = str(row.get('log_type') or '').upper()
                if kind == 'IN':
                    if first is None: first = stamp
                    if opened is None: opened = stamp
                    else: issue('consecutive_in', [row])
                elif kind == 'OUT':
                    last = stamp
                    if opened is not None:
                        chosen.append((opened, stamp)); opened = None
                    else: issue('out_without_in', [row])
                else:
                    issue('unknown_direction', [row])
            if opened is not None: issue('in_without_out', rows[-1:])
            if calc == FIRST_LAST:
                chosen = [(first, last)] if first is not None and last is not None else []
        if calc == FIRST_LAST and len(rows) > 2:
            issue('first_last_includes_breaks', rows)
        if any(hi <= lo or hi - lo > timedelta(hours=24) for lo, hi in chosen):
            issue('invalid_duration', rows); continue
        intervals.extend(chosen)
        sessions.append({'shift': shift, 'shift_start': a.isoformat(), 'shift_end': b.isoformat(),
                         'direction_rule': mode, 'hours_rule': calc, 'punch_count': len(rows),
                         'hours': round(sum((hi-lo).total_seconds()/3600 for lo, hi in chosen), 4),
                         'checkins': [str(r.get('name') or '') for r in rows]})
    return {'intervals': union_intervals(intervals), 'sessions': sessions, 'issues': issues}


def overlay_corrections(intervals, corrections):
    """Replace only each certified authorization window, never the whole workday."""
    accepted, issues = [], []
    for item in corrections:
        try:
            a, b = _as_datetime(item['start']), _as_datetime(item['end'])
            if b <= a or b-a > timedelta(hours=48): raise ValueError('window')
            rows = [(_as_datetime(r['start']), _as_datetime(r['end'])) for r in item['intervals']]
            if any(hi <= lo or lo >= b or hi <= a for lo, hi in rows): raise ValueError('intervals')
            rows = [(max(lo,a),min(hi,b)) for lo,hi in rows]
            if item['kind'] != 'Mark Absent' and not rows: raise ValueError('empty')
            accepted.append((a, b, union_intervals(rows), item))
        except (ValueError, TypeError, KeyError):
            issues.append({'code': 'invalid_correction', 'source': item.get('name')})
    conflicting = set()
    for i, left in enumerate(accepted):
        for j, right in enumerate(accepted[:i]):
            if left[0] < right[1] and right[0] < left[1]: conflicting.update([i, j])
    result, applied = union_intervals(intervals), []
    for i, (a, b, rows, item) in enumerate(accepted):
        if i in conflicting:
            issues.append({'code': 'overlapping_corrections', 'source': item['name']}); continue
        clipped = []
        for lo, hi in result:
            if hi <= a or lo >= b: clipped.append((lo, hi)); continue
            if lo < a: clipped.append((lo, a))
            if hi > b: clipped.append((b, hi))
        result = union_intervals(clipped + rows)
        applied.append({'name': item['name'], 'kind': item['kind'], 'start': a.isoformat(), 'end': b.isoformat(),
                        'intervals': [{'start':lo.isoformat(),'end':hi.isoformat()} for lo,hi in rows]})
    return {'intervals': result, 'applied': applied, 'issues': issues}


def summarize_intervals(intervals, *, week_start, cutoff, threshold):
    # Direct interval accumulation avoids treating contiguous split boundaries as
    # duplicate source punches; these are calculation segments, not Employee Checkins.
    output = reconstruct_week(week_start=week_start, cutoff=cutoff, threshold=threshold, checkins=[])
    from datetime import datetime, time
    start = _as_datetime(week_start)
    start = datetime.combine(start.date(), time.min)
    end = start+timedelta(days=7)
    cut = min(max(_as_datetime(cutoff), start), end)
    for a, b in union_intervals(intervals):
        a, b = max(a, start), min(b, end)
        while a < b:
            stop = min(b, datetime.combine(a.date()+timedelta(days=1), time.min))
            row = output['days'][(a.date()-start.date()).days]
            row['paired_hours'] += (stop-a).total_seconds()/3600
            row['hours_before_cutoff'] += max((min(stop,cut)-a).total_seconds()/3600,0)
            row['status'] = 'paired_evidence'
            a = stop
    output['paired_hours'] = round(sum(d['paired_hours'] for d in output['days']),4)
    output['hours_before_cutoff'] = round(sum(d['hours_before_cutoff'] for d in output['days']),4)
    output['provisional_hours_to_threshold'] = round(max(float(threshold)-output['hours_before_cutoff'],0),4)
    for row in output['days']:
        row['paired_hours'] = round(row['paired_hours'],4)
        row['hours_before_cutoff'] = round(row['hours_before_cutoff'],4)
    return output
