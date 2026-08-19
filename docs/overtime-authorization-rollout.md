# Overtime Authorization — controlled rollout

## Objective

Require overtime to be approved before work begins, then compare that approval
with the employee's shift, Holiday List, and Employee Checkin evidence. This
first phase is intentionally disconnected from Salary Slips, Additional Salary,
Compensatory Leave, and accounting entries.

## Before state

- Employee Checkin captured attendance evidence, but a late punch could not
  establish whether the extra work was authorized.
- Shift Type carried IGC workday flags, Friday end time, and Holiday List data.
- There was no employee overtime-eligibility flag or versioned authorization
  record.
- The existing `Compensatorio` Leave Type and Compensatory Leave Request are
  day/half-day mechanisms, not an auditable hourly bank.

## Exact application change

1. Add the submittable `Overtime Authorization` DocType.
2. Add `Employee.overtime_eligible` (default false) and
   `Employee.overtime_approver` through the idempotent patch
   `powerpro.patches.v1.setup_overtime_authorization`.
3. Add `DGII Payroll Settings.enable_overtime_authorization` (default false).
4. Add a read-only reconciliation endpoint:
   `powerpro.controllers.overtime.get_reconciliation_preview`.
5. Add a pure calculation engine with deterministic tests covering ordinary
   overtime, night hours, breaks, legal holidays, weekly rest, caps, and
   incomplete punches.

The migration creates metadata and an empty authorization table. It does not
mark employees eligible, enable the feature, change historical records, create
salary rows, create leave, or post accounting entries.

## Rules enforced in Phase 1

- Only active employees explicitly marked `Overtime Eligible` may be selected.
- Submission must occur before the authorized start time; retroactive approval
  is rejected.
- The start, end, reason, maximum hours, shift, requester, approver, and approval
  timestamp are preserved on the authorization.
- The effective submitted Shift Assignment is resolved first; the Employee
  default shift is used only when no assignment covers the work date.
- Overlapping non-cancelled authorizations for the same employee are rejected.
- A punch is only evidence. Verified time is limited by the approved window and
  maximum hours.
- On a regular workday, only verified time outside the scheduled shift counts.
- Break intervals are excluded. Missing or unknown punches produce warnings and
  never cause the system to invent hours.
- Legal-holiday work is classified once at +100%, including a legal holiday
  that coincides with weekly rest; premiums are not stacked.
- Ordinary weekly-rest work remains a separate settlement category.
- Regular overtime is split between +35% and +100% using the configured weekly
  extra-hours threshold (or 68 minus expected weekly hours).
- Night hours inside verified overtime are reported separately.

## DEV validation checklist

Record every step in the change-log table below.

1. Deploy the exact app commit to `igcaribe.fortabs.com` and let the normal app
   migration run. Do not run tests, patches, or migrations manually unless the
   deployment failed and the reason has first been diagnosed.
2. Read back app versions, installed apps, the new DocType, Employee custom
   fields, resolved hooks, and relevant scripts/workflows.
3. Confirm the feature flag is off and eligible employee count is zero.
4. Select one active plant operator and one named approver. Capture the before
   values, then set only that employee's two overtime fields.
5. Enable `Enable Overtime Authorization` on DEV and read it back.
6. Create one future authorization, submit it before its start, and verify the
   audit fields. Also verify that a retroactive and an overlapping request are
   rejected.
7. After real or controlled punches exist, run `Reconciliation Preview` and
   compare the result manually with approval, shift, breaks, Holiday List, and
   raw checkins.
8. Confirm zero Salary Slips, Additional Salary records, leave records, and
   accounting entries were created or changed by the preview.

## Validation evidence expected

- Feature flag readback and eligible employee count.
- Submitted authorization with `requested_by`, `approved_by`, and `approved_on`.
- Raw checkins and resolved shift/Holiday List for the test date.
- Preview classification, verified intervals, category hours, warnings, and
  `saved_documents: 0` / `payroll_connected: false`.
- Negative tests for ineligible employee, retroactive approval, overlap, broken
  punch pair, and maximum-hours cap.

## Rollback

Operational rollback is immediate and data-preserving:

1. Clear `Enable Overtime Authorization` in DGII Payroll Settings.
2. Read the field back as false.
3. Preserve existing authorization records as audit evidence.

The patch also exposes
`powerpro.patches.v1.setup_overtime_authorization.disable` for an emergency
server-side disable on a site where that controlled command is available. Do
not delete the DocType or custom fields as a routine rollback.

## Production replication gate

Do not activate this in production until all DEV checklist items pass. Then:

1. Deploy the exact DEV-validated commit through Frappe Cloud.
2. Confirm the production flag remains off after migration.
3. Apply the approved employee/approver list with a before/after record for each
   employee; do not bulk-enable all active employees.
4. Enable the feature and run a one-operator pilot.
5. Independently read back the authorization and preview results.
6. Leave payroll, leave, and accounting integration off until a later phase has
   its own DEV-tested, rollback-ready change set.

## Change-log template

| Field | Required evidence |
| --- | --- |
| Site and environment | Exact site; DEV, staging, or production |
| Timestamp and operator | Who performed the change and when |
| Before state | Record names and exact field values |
| Exact action | UI action, API method, deployment commit, or controlled command |
| After state | Independent readback of the changed values |
| Validation | Positive and negative test result, including raw evidence |
| Rollback | Exact action and readback proving rollback |
| Production replication | Exact commit and approved configuration values |
