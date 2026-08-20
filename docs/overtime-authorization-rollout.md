# Overtime Authorization — controlled rollout

## Objective

Require overtime to be approved before work begins, then compare that approval
with the employee's shift, Holiday List, and Employee Checkin evidence. This
first phase is intentionally disconnected from Salary Slips, Additional Salary,
Compensatory Leave, and accounting entries.

`Planned Settlement` records management's intent only. In Phase 1, an operator
must still perform the reviewed payroll or compensatory-rest action separately;
the authorization preview never creates money, leave, attendance, or ledger
entries. Production users must not treat the preview itself as settlement.

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
- Authorization is blocked unless its resolved Holiday List covers the work
  date, preventing an expired calendar from silently classifying a holiday as a
  regular day.
- A punch is only evidence. Verified time is limited by the approved window and
  maximum hours.
- On a regular workday, only verified time outside the scheduled shift counts.
- Break intervals are excluded. Missing or unknown punches produce warnings and
  never cause the system to invent hours.
- Legal-holiday work is classified once at +100%, including a legal holiday
  that coincides with weekly rest; premiums are not stacked.
- Ordinary weekly-rest work remains a separate settlement category.
- Regular overtime is split between +35% and +100% using the configured total
  weekly-hours threshold. With 44 expected hours and a threshold of 68, the
  +35% band is 24 hours; verified regular overtime above that band is +100%.
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

1. Require a pull request against `develop` with green CI and record its exact
   merge commit.
2. Deploy that exact merge commit through Frappe Cloud using the site's normal
   deployment and migration workflow; do not run patches or migrations again
   manually after a successful deployment.
3. Confirm the production flag remains off after migration and independently
   read back the DocType, Employee custom fields, patch log, and zero-record
   starting state.
4. Apply the approved employee/approver list with a before/after record for each
   employee; do not bulk-enable all active employees.
5. Enable the feature and run a one-operator pilot.
6. Independently read back the authorization and preview results.
7. Leave payroll, leave, and accounting integration off until a later phase has
   its own DEV-tested, rollback-ready change set.

### Production go/no-go checks

Before deployment:

- The feature branch must contain no uncommitted files, have a reviewed PR, and
  have green CI against Frappe, ERPNext, and HRMS version 15.
- DEV must run the exact proposed commit and pass the pure calculation suite,
  metadata/readback checks, authorization controller checks, and read-only
  reconciliation evidence.
- `Weekly Expected Hours` must be positive, and `Max Weekly Extra Hours` must be
  the larger total weekly-hours threshold. IGC uses 44 and 68, producing a
  24-hour +35% band.
- Every pilot employee must have an active Shift Type and a Holiday List that
  covers the authorization date. Production's Shift Type values are the source
  of truth when DEV lacks optional weekday/Friday custom fields.
- The selected approver must be enabled and hold HR Manager, Manufacturing
  Manager, or System Manager.

After deployment but before enablement:

- Confirm Frappe Cloud reports a successful deployment of the exact merge
  commit.
- Confirm `powerpro.patches.v1.setup_overtime_authorization` appears once in
  Patch Log.
- Confirm the feature flag is false, eligible-employee count is zero, and
  Overtime Authorization count is zero.
- Confirm no new Salary Slip, Additional Salary, Attendance, leave, Journal
  Entry, or Payroll Entry was created by deployment.

No-go conditions include failed CI, a failed migration, missing/expired Holiday
List coverage, an invalid 44/68 threshold relationship, an unexpected existing
authorization, or any payroll/leave/accounting mutation during metadata
deployment.

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
