"""Permission-filtered weekly diagnostics used only by the calendar comparison."""
import hashlib
import json
from datetime import datetime, time, timedelta

import frappe
from frappe.utils import get_datetime, getdate

from powerpro.payroll_rules.overtime_weekly import reconstruct_week

LIMIT = 2000


def get_weekly_evidence(doc, weeks, threshold):
    # Called only after the source authorization's read permission has been checked.
    if not frappe.has_permission('Employee Checkin', 'read'):
        return {'available': False, 'weeks': [], 'notes': [
            'No tiene permiso para consultar las marcaciones semanales.'
        ]}
    results = []
    for week in sorted(weeks):
        start = datetime.combine(getdate(week), time.min)
        end = start + timedelta(days=7)
        # One day on either side permits overnight pairs across Monday, never
        # unbounded scans or interpreting a missing boundary punch as absence.
        rows = frappe.get_list('Employee Checkin', filters=[
            ['employee', '=', doc.employee],
            ['time', '>=', start - timedelta(days=1)],
            ['time', '<', end + timedelta(days=1)],
        ], fields=['name', 'time', 'log_type', 'shift', 'offshift', 'modified'],
            order_by='time asc, name asc', limit_page_length=LIMIT + 1)
        if len(rows) > LIMIT:
            results.append({'week_start': week, 'truncated': True, 'complete': False,
                            'settlement_eligible': False})
            continue
        result = reconstruct_week(week_start=start, checkins=rows,
                                  cutoff=max(start, get_datetime(doc.authorization_start)),
                                  threshold=threshold)
        result['source_hash'] = hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode()).hexdigest()
        result['offshift_punches'] = sum(bool(row.get('offshift')) for row in rows if start <= get_datetime(row['time']) < end)
        result['legacy_regular_overtime_before'] = weeks[week]
        results.append(result)
    return {'available': True, 'weeks': results, 'notes': [
        'Son marcaciones actuales visibles para su usuario; pueden diferir de la instantánea de la autorización.',
        'Se suman pares explícitos IN/OUT, descontando los intervalos entre pares. Las secuencias ambiguas se excluyen y se muestran para revisión.',
        'Este diagnóstico aún no aplica la alternancia ni el cálculo de primera entrada y última salida del Shift Type.',
        'El total incluye tiempo dentro y fuera del turno, feriados y descanso. No equivale a horas extras pagables ni certifica una semana completa.',
        'Sin marcaciones no se presume ausencia, una jornada completa ni 44 horas ordinarias. Licencias y verificaciones manuales todavía no completan este diagnóstico.',
        'La distancia al umbral es provisional: depende de las horas reconstruidas antes de la autorización. No cambia las bandas ni los importes de la comparación.',
    ]}
