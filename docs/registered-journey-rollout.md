# Registro de Jornada

Status: implementation prepared; Python adapter and end-to-end staging verification
must precede UI activation. No employee declarations, payments, policy approvals,
or approver replacements are part of this installation.

The coordinator preserves native Work Calls, Retroactive Overtime Adjustments,
Ordinary Night Settlements, Shift Assignments, and Additional Salaries. Work dates
remain independent from the selected payroll date. Preparing a source creates a
draft. Financial approval remains on its native document with its native roles,
evidence freshness checks, policy, and duplicate-claim protection.

Existing attendance resolution, leave/vacation workflows, payroll calculations,
and retainer filters are not replaced by this package.

## Installation

1. Deploy this branch's Python code to the actual PowerPro bench in a staging
   environment first. Restart the relevant application workers using the site's
   normal deployment procedure.
2. Run `bench --site SITE execute powerpro.registered_journey.setup.install`.
   This installs custom schema and matching scripts without enabling new client
   entry points. It refuses to overwrite edited scripts or conflicting schema.
3. Complete the checks below with synthetic employees and an approved test policy.
   Do not use real employees to manufacture test payments on a production site.
4. Deploy the verified version to the intended production site, run installation,
   then enable the three UI scripts through:
   `bench --site SITE execute powerpro.registered_journey.setup.install --kwargs '{"enable_ui": true}'`.

The API refuses preparation when the Python adapter is unavailable. Matching
scripts and schema may already exist from a connector installation; rerunning the
installer preserves them and does not overwrite local edits. The installer has no
automatic migrate hook and does not modify old source documents.

## Behavior

- Payroll Entry and Work Call expose **Registrar Jornada** after UI activation.
- Select employees, actual work window, type of journey, and payroll date.
- **Cambio de Turno** prepares a one-day replacement assignment. It never changes
  the employee's default shift. Approval is explicit and requires native submit
  permission; weekly approved financial dependencies block an unsafe change.
- **Horas Adicionales** chooses future Work Call or historical Retroactive
  Adjustment from the actual work date. The existing approval flow still applies.
- Nocturnidad Ordinaria pays the policy premium on the verified ordinary hours.
  The existing ordinary-night service selects salary, policy and currency; base
  salary is not added again. Additional hours use their separate native source.
- The employee table keeps actions together and links each employee to the
  prepared sources. Retries reuse links. Employee locks serialize preparation and
  overlapping prepared registrations are rejected.
- A managed submitted one-day Shift Assignment keeps historical meaning after
  the scheduler marks it inactive. Cancellation revokes it; unmanaged inactive
  assignments preserve their old behavior.
- An exact declared break can support an ordinary-night settlement without
  fabricating an overtime authorization. Native manual-verification settings,
  native approval roles, calendar checks and fresh evidence still apply. That
  approved physical evidence also contributes to later weekly reconciliation.
- **Descanso Flexible del Turno** records the fact that the configured break is
  taken without fabricating its clock time. Payment remains blocked until its
  diurnal/nocturnal allocation is evidenced or an approved allocation rule exists.
  This package intentionally does not choose that financial rule.

## Verification completed

- Site-free declared-session tests: ordinary night only, break exclusion and
  placement, no fabricated punches, invalid and unfinished windows.
- Adapter tests: historical expiry, cancellation, invalid source links, access,
  unchanged unmanaged assignments, weekly reuse and changed-evidence rejection.
- Existing ordinary-night mathematical regression tests.
- Live connector tests ran with transaction rollback: create/update coordinator,
  review details, stale version rejection, invalid break rejection, missing-adapter
  blocker, and no-op guards for sources outside the new workflow.
- An earlier rollback test checked draft assignment preparation and repeat-call
  reuse. No Payroll Slips, Additional Salaries, Attendance or Checkins were added.

## Required staging gate

The live connector cannot deploy the native Python adapter. These checks remain
required before enabling UI and treating the feature as production-ready:

- Open all three forms and inspect the table on desktop and a narrow viewport.
- Prepare future Work Calls and historical Retroactive Adjustments, including
  overnight windows, mixed journeys, and repeat clicks by concurrent users.
- Submit and cancel an ordinary-only night settlement with exact break evidence;
  verify native Additional Salary links, selected payroll date, cancellation and
  historical review. Confirm that source punches do not change.
- Expire a submitted managed assignment, rebuild the same evidence, then verify
  a later weekly overtime calculation. Confirm no double counting.
- Test native create/submit permissions as an HR user and as an unauthorized user.
- Confirm approved weekly dependencies prevent changing/cancelling the shift.
- Confirm missing policies, incomplete break evidence, incompatible existing
  shifts, closed payrolls, changed evidence and duplicate sources remain blocked.

## Operational limits

One record represents at most 24 hours and 50 employees. Overlapping existing
assignments must be resolved through their normal workflow; the coordinator does
not truncate them. Once source documents exist, their identity and payroll date
are frozen. Corrections that require changing the original registration need an
explicit reversal/replacement workflow; there is no automatic migration of paid
history. Cancelled source links are retained for audit and are not automatically
replaced. Unknown approvers and missing financial policies require HR decisions.

## Rollback

Disable the three new Client Scripts and the registration API to remove the entry
points. Keep schema, links, audit records and source guards. Do not uninstall the
Python adapter while managed approved assignments or settlements exist: their
historical evidence depends on it. Any paid-source reversal must use the native
financial cancellation workflow.
