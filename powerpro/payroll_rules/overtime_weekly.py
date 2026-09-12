"""Conservative weekly punch evidence, independent of payroll and attendance writes.

Explicit IN/OUT pairs are diagnostic evidence, never proof of a complete week.
Do not infer a missed punch, a full scheduled day, or 44 ordinary hours.
"""
from datetime import datetime, time, timedelta
from math import isfinite

from powerpro.payroll_rules.overtime import START_ACTIONS, STOP_ACTIONS, _as_datetime


def reconstruct_week(*, week_start, checkins, cutoff, threshold=68):
    week = datetime.combine(_as_datetime(week_start).date(), time.min)
    if week.weekday():
        raise ValueError('La semana debe comenzar en lunes.')
    end = week + timedelta(days=7)
    cutoff = min(max(_as_datetime(cutoff), week), end)
    threshold = float(threshold)
    if not isfinite(threshold) or threshold <= 0:
        raise ValueError('El umbral semanal debe ser positivo y finito.')
    days = {str((week + timedelta(days=n)).date()): {
        'date': str((week + timedelta(days=n)).date()), 'paired_hours': 0,
        'hours_before_cutoff': 0, 'punch_count': 0, 'issues': [],
    } for n in range(7)}
    issues, intervals = [], []

    def issue(code, rows):
        refs = [str(row.get('name') or '') for row in rows]
        dates = sorted({str(_as_datetime(row['time']).date()) for row in rows})
        issues.append({'code': code, 'checkins': refs, 'dates': dates})
        for day in dates:
            if day in days and code not in days[day]['issues']:
                days[day]['issues'].append(code)

    rows = sorted(checkins, key=lambda r: (_as_datetime(r['time']), str(r.get('name') or '')))
    # Exact duplicate timestamps have no reliable ordering and cannot form a pair.
    duplicate_times = { _as_datetime(rows[i]['time']) for i in range(1, len(rows))
                        if _as_datetime(rows[i]['time']) == _as_datetime(rows[i - 1]['time']) }
    opened, tainted = None, False
    for row in rows:
        stamp = _as_datetime(row['time'])
        day = str(stamp.date())
        if day in days:
            days[day]['punch_count'] += 1
        if stamp in duplicate_times:
            issue('duplicate_timestamp', [row])
            if opened: issue('ambiguous_pair', [opened, row])
            opened, tainted = None, True
            continue
        action = str(row.get('accion') or row.get('log_type') or '').strip().upper()
        if action not in START_ACTIONS | STOP_ACTIONS:
            issue('unknown_direction', [row])
            if opened: issue('ambiguous_pair', [opened, row])
            opened, tainted = None, True
            continue
        if action in START_ACTIONS:
            if opened:
                issue('consecutive_in', [opened, row])
                tainted = True
            else:
                tainted = False
            opened = row
            continue
        if not opened:
            issue('out_without_in', [row])
            tainted = False
            continue
        a, b = _as_datetime(opened['time']), stamp
        if tainted:
            issue('ambiguous_pair', [opened, row])
        elif b <= a or b - a > timedelta(hours=24):
            issue('invalid_duration', [opened, row])
        elif week < b and a < end:
            lo, hi = max(a, week), min(b, end)
            intervals.append({'start': lo.isoformat(), 'end': hi.isoformat(),
                              'checkins': [str(opened.get('name') or ''), str(row.get('name') or '')]})
            while lo < hi:
                stop = min(hi, datetime.combine(lo.date() + timedelta(days=1), time.min))
                item = days[str(lo.date())]
                item['paired_hours'] += (stop - lo).total_seconds() / 3600
                item['hours_before_cutoff'] += max((min(stop, cutoff) - lo).total_seconds() / 3600, 0)
                lo = stop
        opened, tainted = None, False
    if opened:
        issue('in_without_out', [opened])
    before = sum(row['hours_before_cutoff'] for row in days.values())
    total = sum(row['paired_hours'] for row in days.values())
    for row in days.values():
        row['paired_hours'] = round(row['paired_hours'], 4)
        row['hours_before_cutoff'] = round(row['hours_before_cutoff'], 4)
        row['status'] = 'review' if row['issues'] else ('paired_evidence' if row['paired_hours'] else 'no_paired_evidence')
    return {'week_start': str(week.date()), 'week_end': str((end - timedelta(days=1)).date()),
            'cutoff': cutoff.isoformat(), 'paired_hours': round(total, 4),
            'hours_before_cutoff': round(before, 4), 'configured_threshold': threshold,
            'provisional_hours_to_threshold': round(max(threshold - before, 0), 4),
            'complete': False, 'settlement_eligible': False,
            'method': 'explicit_in_out_pairs', 'days': list(days.values()),
            'intervals': intervals, 'issues': issues}
