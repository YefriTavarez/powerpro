# Comparación de horas extras por fecha

Primera entrega del plan de revisión laboral. Incluye un cálculo segmentado y una
comparación de solo lectura; todavía no sustituye la conciliación usada para liquidar.

## Uso

En una **Overtime Authorization** o **Retroactive Overtime Adjustment** guardada,
abrir **Horas extra → Comparar cálculo por fecha**. En una **Overtime Work Call**,
el mismo botón permite elegir una autorización accesible al usuario.

La tabla compara el motor vigente recalculado con el motor segmentado usando la
misma evidencia. No compara automáticamente contra una liquidación histórica:
esa liquidación pudo utilizar otra tarifa, configuración o evidencia.

Muestra horas por categoría, diferencias y detalle de cada fecha. Si el usuario
puede acceder a la tarifa aplicable —o ya está guardada en la liquidación visible—,
muestra importes ilustrativos. No se muestra un total de efectivo si hay descanso
semanal pendiente de definición. No hay botón de guardar, aprobar, pagar o crear licencias.

## Reglas cubiertas

- Divide intervalos al cambiar de fecha y aplica el calendario de cada fecha.
- Descuenta el turno ordinario de los días regulares, incluida la continuación de
  un turno nocturno anterior cuando corresponde.
- Aplica el máximo autorizado una vez a toda la ventana, en orden cronológico.
- Conserva las pausas observadas y separa los acumulados de semanas distintas.
- Cuenta solapamientos con el horario nocturno con precisión de segundos antes
  del redondeo de presentación.
- Falla si falta cobertura de calendario o hay intervalos inválidos/superpuestos.

## Evidencia y límites

Los documentos sin conciliación usan marcaciones actuales. Las instantáneas con
marcaciones usan las guardadas. Las verificaciones manuales usan sus intervalos
guardados; si sólo existen intervalos ya recortados, se avisa de esa limitación.
La asistencia presumida requiere revisión y no se convierte en evidencia real.

Ventanas de hasta 48 horas, dentro de las dos fechas cubiertas por el lector
actual de marcaciones. La comparación no infiere que un ponche ausente sea ausencia
laboral. Las advertencias de marcaciones se muestran, sin declarar validación.

Se conservan las tasas, bandas semanales y regla de solapamiento nocturno actuales.
Quedan pendientes la clasificación de jornada nocturna completa, la combinación
legal de recargos, el total semanal de todas las fuentes y el flujo completo de
descanso semanal. El calendario de la comparación es el actualmente configurado;
no es una reconstrucción garantizada del calendario histórico.

El resultado incluye versión, huella de entradas, contexto por fecha y origen de
evidencia. No se persiste. Los permisos se comprueban antes de leer evidencia; la
lista de autorizaciones utiliza filtros de permisos y cada comparación vuelve a
comprobar el documento. Los importes requieren acceso a la asignación salarial
efectiva cuando la tarifa no está ya en la liquidación visible.

## Pruebas

```sh
python3 tests/test_overtime_calendar.py
node tests/test_overtime_calendar_ui.cjs
python3 -m unittest discover -s powerpro/payroll_rules -p 'test_overtime*.py'
```

Son pruebas locales, sin base de datos. La verificación en Desarrollo debe comprobar
el endpoint con permisos reales, assets y ausencia de escrituras. No ejecutar jobs
de liquidación ni crear documentos pagables para comprobar esta vista previa.

## Instalación y reversión

Sólo añade módulos Python, un asset JS y un botón en tres formularios; no cambia
esquema, fixtures, configuración de tasas ni métodos del scheduler/liquidación.
Tras desplegar en Desarrollo, limpiar caché del sitio y recargar los formularios.
Las nuevas respuestas se obtienen únicamente al solicitar la comparación.

Para revertir, retirar el commit de esta entrega preservando cambios ajenos, limpiar
caché y recargar. No hay documentos de negocio que revertir por usar la comparación.

## Weekly evidence diagnostic (v2)

The same dialog now shows a permission-filtered, current Employee Checkin diagnostic
for each Monday–Sunday week touched by the authorization. This is separate from the
saved evidence used to compare the authorization's hours and amounts. It does not
replace the existing 44-to-68 hour band or change settlement.

It sums explicit, non-ambiguous IN/OUT pairs, excludes breaks between pairs, clips
intervals at week boundaries, and splits totals by calendar date. It shows the total
before the authorization, the configured total-hours threshold, the provisional gap,
and the prior regular overtime used by the existing implementation. These quantities
are deliberately labelled separately: total work and regular overtime are not equal.

Consecutive IN marks, missing partners, unknown directions, duplicate timestamps,
and pairs longer than 24 hours produce review issues. Ambiguous pairs contribute no
hours. The 24-hour guard is a diagnostic validity boundary, not a legal work limit.
One calendar day on either side permits overnight boundary pairs. A limit of 2,000
permission-visible punches per nine-day employee query prevents unbounded scans;
truncated sets produce no totals. No user can read weekly punches solely by gaining
access to an authorization: Employee Checkin read and list permissions apply.

Completeness and settlement eligibility always remain false. Permission filtering,
missing/late punches, unrecorded breaks and corrected manual evidence can affect the
total. No missing date becomes an absence or a presumed full day. This first weekly
stage does not apply Shift Type alternation/first-last rules, combine manual approvals
or certify synchronization completeness; those are necessary subsequent steps before
weekly evidence can drive payroll. All dates use the site's existing local datetimes.

Validation: `python3 tests/test_overtime_weekly.py`, the calendar tests above, and
`node tests/test_overtime_calendar_ui.cjs`. Deployment is code-only; no migration,
new fields, Attendance generation or historical salary updates are needed. Revert
the weekly evidence commit and clear the explicit Development site's cache to roll
back this stage.

## Shift interpretation and HR corrections (v3)

The weekly preview now compares three separate readings: conservative explicit
IN/OUT pairs; current Shift Type options applied to captured shift sessions; and
those configured intervals with current, audited HR corrections. The original
calendar amounts and settlement engine remain unchanged.

Sessions are grouped by the shift name/start/end saved on Employee Checkin. These
capture the assignment resolved when the punch was saved; the preview does not
reassign historical punches from today's Employee default shift. Off-shift,
skip-auto-attendance and missing-window punches are listed for review. An overtime
authorization does not yet expand a captured shift's window.

All four combinations of alternating/strict direction and first-last/every-valid-
pair calculations are supported. First-last intentionally includes intermediate
break time, matching the meaning of the HRMS option. Alternating first-last uses
first/last even with an odd count, but prominently flags the odd count. Reinterpreted
directions remain unchanged in the stored Checkins. Duplicate timestamps and
invalid durations are excluded rather than forced into a session. Hours retain
second precision until the preview rounds to four decimals; HRMS's attendance
helper rounds individual contributions to two decimals, so small rounding
variations can occur. Session unions prevent overlap from double counting.

Manual Verification is taken from currently submitted, permission-visible Overtime
Authorizations with reconciliation user/date. HR exceptions must be the current
linked event, Applied, matching the employee/authorization, and have resolver/date.
Pending corrections, unconfirmed events and Cancel Participation do not change the
evidence. Correct Worked Hours replaces its authorization window; Mark Absent
removes only that window, never the ordinary workday. Raw manual intervals may
extend outside the authorization; only their overlapping portion is used here.
Overlapping correction windows are all flagged and left unapplied, with no arbitrary
priority. Presumed Attendance is never used as worked evidence.

This does not certify weekly completeness or eligibility for settlement. Remaining
work includes overnight authorization-aware grouping, synchronization/coverage,
manual correction conflicts and the legal policy decisions in the original plan.
Current Shift Type options are not an immutable historical settings snapshot.

Additional tests: `python3 tests/test_overtime_shift_evidence.py` (pure, no site).
Rollback: revert the v3 commit and clear the explicit Development site's cache.

## Overnight authorization proposal (v4)

Submitted Overtime Authorizations crossing midnight now show a separate overnight
proposal. It anchors to a captured same-day shift ending no later than the authorized
start, and extends that session only in memory, up to the authorized end. The full
extended session has a conservative 24-hour diagnostic boundary. The displayed
intervals describe work evidence, including ordinary time, not payable OT totals.

Eligible punches after the ordinary shift can join that proposed session if they
are outside the following shift's reception window. Following windows use current
active Shift Assignments, Employee default shift when unassigned, and captured
windows on following-day punches. A competing next-shift window, overlapping
submitted authorization or incomplete permission-visible context prevents an
unambiguous proposal. Hidden record IDs are never returned; internal bounded ID
checks prevent treating a permission-filtered subset as complete evidence.

The interpreter honors the Shift Type's strict/alternating direction rule. An IN
reinterpreted by alternation remains IN in the database and carries a review warning.
Strict mode does not silently relabel it. Missing start/exit punches are never
synthesized. Original skip-auto-attendance flags remain effective. Future windows,
missing/stale synchronization and invalid sequences are explicit blockers.

The source digest includes visible punches, assignments and policies. No attendance,
authorization, payment, or scheduling setting is saved. `settlement_eligible` remains
false even when the proposal has no blockers: synchronization alone does not prove
attendance, and weekly/legal settlement policy is still a separate gate.

Development readback on 2026-09-11: all 79 punches had skip_auto_attendance=1 and
were created within one second on 2026-08-19. No Version, Comment, Data Import or
Server Script supplied an explanation. This is consistent with a batch load but
its origin and intent are unconfirmed; no flags were cleared based on that inference.

Additional tests: `python3 tests/test_overtime_overnight.py`. The service requires
read access to the employee, checkins, shift assignments and shift policies. Draft
authorizations and retroactive adjustments are not treated as prior overnight
approval. Rollback is code-only: revert the v4 commit and clear the Development
site's cache. No migration or historical attendance generation is needed.
