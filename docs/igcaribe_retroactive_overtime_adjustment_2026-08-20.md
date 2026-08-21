# IGC Retroactive Overtime Adjustment change record — 2026-08-20

## Target context

- Repository: `YefriTavarez/powerpro`
- Base: `origin/develop` at `ca3659b`
- Implementation branch: `agent/retroactive-overtime-adjustment`
- Intended site: `igcaribe.com` (production, Frappe Cloud)
- Local implementation only at the time of this record; no site records or settings changed.

## Before state

- `Overtime Authorization` enforces approval before the authorized work begins.
- Historical Employee Checkins cannot be converted into an approved authorization.
- Reconciliation is read-only and does not create Salary Slip, Additional Salary,
  leave, or accounting records.
- There is no separate historical-exception DocType.

## Change

### New DocType

`Retroactive Overtime Adjustment` (`OT-ADJ-.YYYY.-.#####`) is a submittable,
tracked exception record. It reuses the effective employee, approver, shift,
Holiday List, day-classification, punch-pairing, weekly-band, and night-hour
rules from `Overtime Authorization`.

Submission requires all of the following:

1. Normal overtime authorization is enabled.
2. Retroactive adjustment is separately enabled.
3. The submission date is on or before the configured deadline.
4. The Work Date falls inside the configured closed historical period.
5. The reviewed window has already ended.
6. The employee is Active, overtime-eligible, and has an enabled authorized
   approver.
7. The resolved Holiday List covers the Work Date.
8. The reviewed window is valid and does not overlap an active Overtime
   Authorization or Retroactive Overtime Adjustment.
9. The assigned approver submits the record.
10. Existing Employee Checkins produce more than zero verified hours inside the
    reviewed window and maximum-hour cap.

On submission the adjustment stores an immutable reconciliation snapshot:

- verified hours;
- regular +35% and +100% hours;
- legal-holiday, weekly-rest, and night hours;
- warnings;
- verified intervals;
- source Employee Checkin names, times, actions, and shifts;
- reconciliation and approval users/timestamps.

The snapshot remains operational evidence only. It does not create payroll,
leave, or accounting documents.

### New DGII Payroll Settings fields

- `enable_retroactive_overtime_adjustment` — defaults to disabled.
- `retroactive_overtime_from_date` — earliest eligible Work Date.
- `retroactive_overtime_to_date` — latest eligible Work Date.
- `retroactive_overtime_submission_deadline` — automatic closure date.

### Existing code touched

- The read-only reconciliation controller now serializes source check-in
  evidence and includes submitted retroactive snapshots in the same weekly
  overtime-band context.
- The existing overtime emergency-disable helper also disables the retroactive
  gate while preserving all audit records.
- Spanish translations were added for the new UI and validation messages.

## Validation

- JSON schemas parse successfully.
- Python sources compile successfully.
- Existing pure overtime rules: 14 tests passed.
- New retroactive policy rules: 3 tests passed.
- `git diff --check`: passed.
- Full Frappe runtime validation remains required on DEV after deployment.

## Production replication

1. Merge the implementation branch to `develop` after review.
2. Deploy `develop` through Frappe Cloud. The normal deployment migration must
   install the standard DocType and DGII Payroll Settings fields.
3. Read back the deployed app commit and effective DocType metadata.
4. Confirm the new feature remains disabled and adjustment count is zero.
5. In DGII Payroll Settings, configure the approved historical period and a
   short submission deadline.
6. Enable normal overtime authorization and the separate retroactive gate.
7. Mark only approved plant employees as overtime-eligible and confirm their
   assigned approvers.
8. Run one historical Francis record as the controlled pilot. Preview first;
   compare the source check-ins and calculated hours; then submit only after
   management confirms the exception.
9. Verify no Salary Slip, Additional Salary, Leave Application, Leave
   Allocation, Payroll Entry, or Journal Entry was created.
10. Close the exception path by disabling the retroactive gate when the initial
    backlog is complete or the deadline expires.

## Rollback

Immediate non-destructive rollback:

1. Clear `Enable Retroactive Overtime Adjustment` in DGII Payroll Settings.
2. Preserve all submitted adjustment records and their snapshots.
3. Cancel only an individual adjustment that management explicitly determines
   is invalid; do not delete audit records.

Code rollback before any adjustments exist:

1. Revert the implementation commit and redeploy through Frappe Cloud.
2. Confirm the feature flag is disabled before rollback.

If submitted adjustments exist, prefer disabling the feature and reverting
business behavior without removing the DocType or its database table.

## Production risks

- Incorrect historical shift or Holiday List configuration can misclassify the
  day or scheduled hours.
- Checkins prove recorded presence intervals, not the business necessity for
  overtime; the exception justification and approver remain mandatory.
- Changing source check-ins after submission does not change the immutable
  snapshot. Any correction must use cancellation and amendment with an audit
  explanation.
- Leaving the temporary gate enabled indefinitely weakens the preapproval
  control. The configured deadline and final manual disablement are mandatory
  rollout controls.

## 2026-08-21 — Draft reconciliation preview fix

### Before state

- A Draft adjustment displayed the submitted-snapshot fields as zero.
- The supervisor had to open `Overtime > Preview Reconciliation` to see the
  actual calculated hours.
- Choosing Cash or Compensatory Rest changed only the operational preference;
  it did not make the calculated hours visible on the form.

### Change

- Branch: `agent/retroactive-overtime-draft-preview`
- Base: merged production source `origin/develop` at `dfcaac4`.
- A saved Draft now loads a read-only reconciliation preview automatically.
- The preview shows verified hours, configured percentage rates, hour
  categories, verified intervals, warnings, and the selected settlement note.
- Calculation-related edits mark the preview stale and instruct the operator
  to save before relying on a recalculation.
- The zero-value submitted-snapshot fields are hidden while the document is a
  Draft. They appear only after submission or cancellation.
- Submission still performs the authoritative server-side recalculation and
  stores the immutable snapshot. No Draft calculation is persisted as approval
  evidence.

### Validation

- JavaScript syntax: passed.
- Draft-preview renderer smoke test: passed for two hours at the configured
  +35% rate, Cash settlement, interval rendering, and zero warnings.
- DocType JSON and Draft/submitted visibility assertions: passed.
- Spanish translation CSV structure: passed.
- Pure overtime rules: 14 tests passed.
- Retroactive policy rules: 3 tests passed.
- Python compilation and `git diff --check`: passed.

### Production deployment and verification

1. Merge the fix branch after review and deploy it through the normal Frappe
   Cloud `Deploy and Update` flow so the standard DocType metadata is reloaded.
2. Do not run tests directly against production.
3. Open a saved Draft adjustment and verify the preview appears without using
   the Overtime menu.
4. Confirm the preview shows current configured rates, calculated hours,
   intervals, warnings, and the settlement note.
5. Change a calculation input and confirm the form asks for a save before
   recalculating.
6. Submit only after reviewing the preview; verify the same calculation is
   stored in the submitted snapshot.
7. Confirm the deployment creates no Salary Slip, Additional Salary, Leave
   Allocation, Payroll Entry, or Journal Entry.

### Rollback

1. Revert the fix commit and redeploy through the normal Frappe Cloud flow.
2. Existing submitted adjustment snapshots remain unchanged.
3. If an immediate operational fallback is needed before redeployment, use the
   existing `Overtime > Preview Reconciliation` action and keep the retroactive
   feature gate disabled for new approvals.
