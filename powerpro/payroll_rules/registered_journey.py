"""Physical declarations for a registered journey; no monetary or policy defaults."""
from powerpro.payroll_rules.overtime import _as_datetime
from powerpro.payroll_rules.overtime_manual_session import validate_manual_intervals


def declared_session(record, row, lower, upper, now):
    mode = row.get('break_mode') or 'Marcaciones'
    if mode == 'Marcaciones':
        return None
    if mode == 'Descanso Flexible del Turno':
        raise ValueError('El descanso flexible requiere evidencia de su distribución diurna y nocturna o una regla aprobada; no se presume su ubicación.')
    if mode != 'Descanso Declarado':
        raise ValueError('Seleccione un modo de descanso válido.')
    required = ('actual_start', 'actual_end', 'break_start', 'break_end', 'evidence_reference')
    if any(not row.get(key) for key in required) or not str(row.get('evidence_reference') or '').strip():
        raise ValueError('Complete el horario real, el descanso y la referencia de la declaración.')
    start, end = _as_datetime(row['actual_start']), _as_datetime(row['actual_end'])
    pause_start, pause_end = _as_datetime(row['break_start']), _as_datetime(row['break_end'])
    recorded_start, recorded_end = _as_datetime(record['starts_at']), _as_datetime(record['ends_at'])
    if any(value.tzinfo for value in (start, end, pause_start, pause_end, recorded_start, recorded_end)):
        raise ValueError('Use la hora local del sitio sin sufijo de zona horaria.')
    if not recorded_start <= start <= pause_start < pause_end <= end <= recorded_end:
        raise ValueError('El descanso y el horario real deben estar dentro de la jornada registrada.')
    intervals = []
    if start < pause_start:
        intervals.append({'start': str(start), 'end': str(pause_start)})
    if pause_end < end:
        intervals.append({'start': str(pause_end), 'end': str(end)})
    declaration = {'full_session': True, 'reference': record['name'] + ' · ' + row['evidence_reference'].strip(), 'intervals': intervals}
    validate_manual_intervals(declaration, lower, upper, now)
    return declaration
