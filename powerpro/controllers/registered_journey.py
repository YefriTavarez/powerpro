"""Optional adapter for Registro de Jornada; legacy documents keep native paths."""
import frappe
from frappe.utils import getdate, get_datetime, now_datetime
from powerpro.payroll_rules.registered_journey import declared_session

VERSION = 1


@frappe.whitelist()
def capabilities():
    frappe.has_permission('Registro de Jornada', 'read', throw=True)
    return {'version': VERSION, 'historical_shift': True, 'ordinary_declaration': True}


def source_row(doc, *, for_update=False):
    name = doc.get('custom_igc_journey')
    if not name:
        return None, None
    record = frappe.get_doc('Registro de Jornada', name, for_update=for_update)
    record.check_permission('read')
    matches = [row for row in record.employees if row.name == doc.get('custom_igc_journey_row')]
    if len(matches) != 1 or doc.get('custom_igc_journey_key') != record.name + '|' + matches[0].name:
        frappe.throw('El documento no corresponde al Registro de Jornada indicado.')
    row = matches[0]
    if doc.employee != row.employee or getdate(doc.work_date) != getdate(record.starts_at):
        frappe.throw('El empleado o la fecha no corresponden al Registro de Jornada.')
    return record, row


def ordinary_declaration(doc, shift, lower, upper, *, for_update=False):
    record, row = source_row(doc, for_update=for_update)
    if record is None:
        return None
    if record.company != frappe.db.get_value('Employee', doc.employee, 'company'):
        frappe.throw('La jornada pertenece a otra empresa.')
    if record.journey_type != 'Horas Adicionales' and record.replacement_shift != shift:
        frappe.throw('El turno aplicado no coincide con la jornada registrada.')
    try:
        declaration = declared_session(record.as_dict(), row.as_dict(), lower, upper, now_datetime())
    except ValueError as error:
        frappe.throw(str(error))
    if declaration is None:
        return None
    return {'registration': record.name, 'row': row.name, 'manual_declaration': declaration,
            'worked_intervals': [{'start': get_datetime(r['start']).isoformat(), 'end': get_datetime(r['end']).isoformat()} for r in declaration['intervals']]}


def shift_assignments(employee, through, *, for_update=False, include_modified=False):
    """A submitted managed one-day assignment retains historical meaning after expiry.

    Cancelling it removes it from this query. Unmanaged inactive assignments retain
    their previous behavior. Status/modified are not frozen into managed evidence:
    the nightly expiry job may update them without changing the approved schedule.
    """
    from powerpro.controllers.overtime import _reconciliation_rows
    fields = ['name', 'shift_type', 'start_date', 'end_date']
    if include_modified:
        fields.append('modified')
    filters = {'employee': employee, 'docstatus': 1, 'start_date': ['<=', through]}
    managed = frappe.get_meta('Shift Assignment').has_field('custom_igc_journey')
    if managed:
        fields += ['status', 'custom_igc_journey', 'custom_igc_journey_row', 'custom_igc_journey_key']
    rows = _reconciliation_rows('Shift Assignment', for_update=for_update, filters={**filters, 'status': 'Active'},
                               fields=fields, limit=1001)
    if managed:
        rows += _reconciliation_rows('Shift Assignment', for_update=for_update,
            filters={**filters, 'status': ['!=', 'Active'], 'custom_igc_journey': ['is', 'set']},
            fields=fields, limit=1001)
    if len(rows) > 1000:
        frappe.throw('Demasiadas asignaciones de turno; requiere revisión.')
    result = []
    for row in rows:
        if managed and row.get('custom_igc_journey'):
            record = frappe.get_doc('Registro de Jornada', row.custom_igc_journey, for_update=for_update)
            record.check_permission('read')
            members = [r for r in record.employees if r.name == row.custom_igc_journey_row and r.employee == employee]
            day = getdate(record.starts_at)
            if (len(members) != 1 or members[0].shift_assignment != row.name
                    or row.custom_igc_journey_key != record.name + '|' + members[0].name
                    or not row.end_date or getdate(row.start_date) != day or getdate(row.end_date) != day
                    or record.replacement_shift != row.shift_type or record.journey_type == 'Horas Adicionales'):
                frappe.throw('La asignación temporal ya no coincide con su jornada registrada.')
            row.pop('modified', None)
        elif managed and row.status != 'Active':
            continue
        for key in ['status', 'custom_igc_journey', 'custom_igc_journey_row', 'custom_igc_journey_key']:
            row.pop(key, None)
        result.append(row)
    return result


@frappe.whitelist()
def resolve_shift(employee, day):
    person = frappe.get_doc('Employee', employee)
    person.check_permission('read')
    date = getdate(day)
    rows = [r for r in shift_assignments(employee, date) if not r.end_date or getdate(r.end_date) >= date]
    names = {r.shift_type for r in rows}
    if len(names) > 1:
        frappe.throw('Hay asignaciones de turno superpuestas; revíselas primero.')
    rows.sort(key=lambda r: (getdate(r.start_date), r.name), reverse=True)
    return {'name': rows[0].name if rows else None, 'shift': rows[0].shift_type if rows else person.default_shift}


def ordinary_week_evidence(employee, first, cutoff, *, for_update=False):
    """Reuse approved standalone ordinary declarations for later weekly evidence."""
    result = {'intervals': [], 'checkins': [], 'sessions': [], 'issues': []}
    dt = 'Ordinary Night Settlement'
    if not frappe.db.exists('DocType', dt) or not frappe.get_meta(dt).has_field('custom_igc_journey'):
        return result
    from powerpro.controllers.overtime import _reconciliation_rows
    from powerpro.controllers.ordinary_night import build_preview
    from powerpro.controllers.checkin_overtime import _evidence_hash
    names = _reconciliation_rows(dt, for_update=for_update,
        filters={'employee': employee, 'docstatus': 1, 'custom_igc_journey': ['is', 'set'],
                 'work_date': ['between', [first, getdate(cutoff)]]}, pluck='name', limit=51)
    if len(names) > 50:
        frappe.throw('Demasiadas liquidaciones nocturnas semanales; requiere revisión.')
    for name in names:
        doc = frappe.get_doc(dt, name, for_update=for_update)
        doc.check_permission('read')
        saved = frappe.parse_json(doc.evidence_snapshot or '{}')
        data = saved.get('input') or {}
        if not (data.get('certified_session') or {}).get('registration'):
            continue
        if not saved.get('worked_intervals') or any(get_datetime(r['end']) > get_datetime(cutoff) for r in saved['worked_intervals']):
            continue
        try:
            fresh = build_preview(doc, for_update=for_update)
        except frappe.ValidationError:
            fresh = {}
        if (fresh.get('state') != 'Verified' or fresh.get('input_hash') != saved.get('input_hash')
                or _evidence_hash(fresh.get('worked_intervals')) != _evidence_hash(saved['worked_intervals'])):
            result['issues'].append({'code': 'weekly_previous_snapshot_changed', 'source_type': dt, 'authorization': name})
            continue
        result['intervals'].extend(fresh['worked_intervals'])
        result['checkins'].extend(r['name'] for r in fresh['source_checkins'])
        context = fresh['input']['context']
        result['sessions'].append({'shift': fresh['input']['shift']['name'],
                                   'start': str(context['shift_start']), 'end': str(context['shift_end'])})
    return result
