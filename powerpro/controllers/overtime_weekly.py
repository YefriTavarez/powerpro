"""Permission-filtered weekly diagnostics used only by the calendar comparison."""
import hashlib
import json
from datetime import datetime, time, timedelta

import frappe
from frappe.utils import get_datetime, getdate

from powerpro.payroll_rules.overtime_weekly import reconstruct_week
from powerpro.payroll_rules.overtime_shift_evidence import interpret_shift_punches, overlay_corrections, summarize_intervals

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
        ], fields=['name', 'time', 'log_type', 'shift', 'offshift', 'modified',
                    'shift_start', 'shift_end', 'shift_actual_start', 'shift_actual_end', 'skip_auto_attendance'],
            order_by='time asc, name asc', limit_page_length=LIMIT + 1)
        if len(rows) > LIMIT:
            results.append({'week_start': week, 'truncated': True, 'complete': False,
                            'settlement_eligible': False})
            continue
        result = reconstruct_week(week_start=start, checkins=rows,
                                  cutoff=max(start, get_datetime(doc.authorization_start)),
                                  threshold=threshold)
        result['shift_comparison'] = _shift_comparison(doc, rows, start, end, threshold)
        result['source_hash'] = hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode()).hexdigest()
        result['offshift_punches'] = sum(bool(row.get('offshift')) for row in rows if start <= get_datetime(row['time']) < end)
        result['legacy_regular_overtime_before'] = weeks[week]
        results.append(result)
    return {'available': True, 'weeks': results, 'notes': [
        'Son marcaciones actuales visibles para su usuario; pueden diferir de la instantánea de la autorización.',
        'Se suman pares explícitos IN/OUT, descontando los intervalos entre pares. Las secuencias ambiguas se excluyen y se muestran para revisión.',
        'La lectura explícita IN/OUT se conserva para compararla con las reglas actuales del turno y las correcciones aplicadas.',
        'El total incluye tiempo dentro y fuera del turno, feriados y descanso. No equivale a horas extras pagables ni certifica una semana completa.',
        'Sin marcaciones no se presume ausencia, una jornada completa ni 44 horas ordinarias. Las verificaciones manuales solo reemplazan su ventana autorizada; las licencias no acreditan horas trabajadas.',
        'La distancia al umbral es provisional: depende de las horas reconstruidas antes de la autorización. No cambia las bandas ni los importes de la comparación.',
    ]}


def _shift_comparison(doc, rows, start, end, threshold):
    names = sorted({r.get('shift') for r in rows if r.get('shift')})
    policies = []
    if names and frappe.has_permission('Shift Type', 'read'):
        policies = frappe.get_list('Shift Type', filters={'name': ['in', names]},
            fields=['name','modified','determine_check_in_and_check_out','working_hours_calculation_based_on'],
            limit_page_length=len(names))
    interpreted = interpret_shift_punches(rows, {r['name']: r for r in policies})
    corrections, notes = _corrections(doc, start, end)
    adjusted = overlay_corrections(interpreted['intervals'], corrections)
    args = dict(week_start=start, cutoff=max(start, get_datetime(doc.authorization_start)), threshold=threshold)
    plain = summarize_intervals(interpreted['intervals'], **args)
    corrected = summarize_intervals(adjusted['intervals'], **args)
    return {'configured': plain, 'with_corrections': corrected,
            'sessions': interpreted['sessions'], 'issues': interpreted['issues'] + adjusted['issues'],
            'applied_corrections': adjusted['applied'], 'policies': policies, 'notes': notes + [
                'Se utiliza el turno y horario guardado en cada marcación; no se reasigna usando el turno actual del empleado.',
                'Las opciones del Shift Type son las actuales, no una instantánea histórica. Primera entrada/última salida puede incluir descansos.',
                'Marcas fuera de turno o sin horario guardado requieren revisión; una autorización nocturna aún no extiende automáticamente estos grupos.',
                'La alternancia interpreta direcciones dentro del mismo turno sin modificar Employee Checkin. Cantidades impares siguen señaladas para revisión.',
                'Estos resultados siguen siendo provisionales: no certifican cobertura ni habilitan liquidación.',
            ]}


def _corrections(doc, start, end):
    notes, accepted = [], []
    if not frappe.has_permission('Overtime Authorization', 'read'):
        return [], ['No hay acceso a las verificaciones de otras autorizaciones.']
    sources = frappe.get_list('Overtime Authorization', filters=[
        ['employee','=',doc.employee], ['docstatus','=',1],
        ['authorization_start','<',end], ['authorization_end','>',start],
        ['reconciliation_source','in',['Manual Verification','HR Exception']],
    ], fields=['name','employee','authorization_start','authorization_end','reconciliation_source',
               'reconciled_by','reconciled_on','manual_worked_intervals','attendance_exception','auto_status'],
        order_by='authorization_start asc, name asc', limit_page_length=101)
    if len(sources) > 100:
        return [], ['Demasiadas correcciones: no se aplica un conjunto truncado.']
    event_names = [r.get('attendance_exception') for r in sources if r.get('attendance_exception')]
    events = {}
    if event_names and frappe.has_permission('Overtime Attendance Exception', 'read'):
        events = {r['name']: r for r in frappe.get_list('Overtime Attendance Exception',
            filters={'name':['in',event_names]}, fields=['name','authorization','employee','status',
                'action','worked_intervals','resolved_by','resolved_on'], limit_page_length=len(event_names))}
    for source in sources:
        if source.get('auto_status') == 'Correction Pending':
            notes.append('Corrección pendiente excluida: '+source['name']); continue
        if not source.get('reconciled_by') or not source.get('reconciled_on'):
            notes.append('Verificación sin auditoría excluida: '+source['name']); continue
        raw, kind, name = None, None, source['name']
        if source.get('reconciliation_source') == 'Manual Verification':
            raw, kind = source.get('manual_worked_intervals'), 'Manual Verification'
        elif source.get('reconciliation_source') == 'HR Exception':
            event = events.get(source.get('attendance_exception'))
            if not event or event.get('status') != 'Applied' or event.get('authorization') != source['name'] or event.get('employee') != doc.employee or not event.get('resolved_by') or not event.get('resolved_on'):
                notes.append('Excepción sin aplicación auditable o acceso excluida: '+source['name']); continue
            kind = event.get('action')
            if kind not in {'Correct Worked Hours','Mark Absent'}:
                notes.append('Cancelar participación no confirma ausencia: '+source['name']); continue
            name = event['name']
            raw = '[]' if kind == 'Mark Absent' else event.get('worked_intervals')
        try:
            parsed = frappe.parse_json(raw or '[]')
            if not isinstance(parsed, list) or any(not isinstance(r, dict) for r in parsed): raise ValueError('intervals')
        except (ValueError, TypeError):
            notes.append('Intervalos de corrección ilegibles: '+name); continue
        accepted.append({'name':name,'kind':kind,'start':source['authorization_start'],
                         'end':source['authorization_end'],'intervals':parsed})
    return accepted, notes
