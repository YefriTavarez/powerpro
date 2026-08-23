# IGC Retroactive Overtime Cash Settlement

## Target context

- Application: PowerPro
- Development site: `igcaribe.fortabs.com`
- Production site: `igcaribe.com` on Frappe Cloud
- DEV bench: `/opt/erpnext/igcaribe-bench`
- DEV versions read back on 2026-08-23: Frappe 15.103.2, ERPNext 15.102.0,
  HRMS 15.58.5, PowerPro 1.0.1
- Implementation branch: `agent/retroactive-overtime-cash-settlement`

Production data must not be changed merely by deploying this release. Existing
approved adjustments are not backfilled automatically.

## Before state

`Retroactive Overtime Adjustment` stored an approval and an immutable punch
reconciliation snapshot. `Planned Settlement = Cash` was informational only.
It did not create `Additional Salary`, populate Salary Slip overtime inputs, or
create a payroll earning.

The controller also required Reviewed Start to match Work Date but did not
limit Reviewed End to the same work date. A daytime adjustment could therefore
span several dates and combine unrelated check-in intervals before reaching
its hour cap.

## Exact application change

### One-date guardrail

- A daytime adjustment must start and end on Work Date.
- A Shift Type whose configured end time is on the following day may end on
  that following date, but never later.
- The same guard is rerun before explicitly settling a pre-release approved
  adjustment. A legacy multi-day record cannot enter payroll.

### Cash calculation

The submitted Salary Structure Assignment effective on Work Date supplies the
hourly rate. If a legacy assignment has no populated `salary_per_hour`, the
existing PowerPro calculation (`base / 23.83 / 8`, rounded to two decimals) is
used without modifying the assignment.

The configured DGII Payroll Settings rates supply the premiums:

- `Horas Extras 35%`: regular +35% hours × hourly rate × 1.35;
- `Horas Extras 100%`: regular +100% plus legal-holiday +100% hours × hourly
  rate × 2.00;
- `Horas Nocturnas`: verified night hours × hourly rate × 0.15.

The actual configured percentages are used rather than hard-coded percentages.
The multipliers above illustrate the currently configured 35%, 100%, and 15%.

Ordinary weekly-rest hours remain outside automatic cash settlement. A Cash
submission containing them is blocked and must be changed to Compensatory Rest
or have its day classification corrected. A legal holiday on weekly rest is
already classified once as legal-holiday +100%.

### Payroll records

Submitting a new approved Cash adjustment creates and submits one non-recurring
Additional Salary record for every non-zero settlement component. Each record:

- uses Work Date as Payroll Date;
- has `overwrite_salary_structure_amount = 0`;
- links back through `ref_doctype = Retroactive Overtime Adjustment` and
  `ref_docname = <adjustment>`;
- is pulled by standard HRMS Salary Slip processing for the payroll period.

A row lock on the source adjustment plus a reference lookup prevents duplicate
settlement during retries or simultaneous requests.

### Status and rollback controls

- `Pending`: no payroll records created.
- `Created`: linked Additional Salary records exist and are submitted.
- `Paid`: a submitted Salary Slip contains every linked Additional Salary.
- Cancelling that Salary Slip returns the adjustment to `Created`.
- A `Paid` adjustment cannot be cancelled until its Salary Slip is cancelled.
- Cancelling an unpaid adjustment cancels its linked Additional Salary records.
- Linked Additional Salary records cannot be cancelled directly while their
  source adjustment remains submitted.

## Operator workflow

1. Save a single-work-date adjustment.
2. Review the draft hours, configured rates, hourly rate, line amounts, total,
   warnings, verified intervals, and source check-ins.
3. Select Cash or Compensatory Rest.
4. The assigned approver submits the adjustment.
5. For Cash, verify Settlement Status is `Created` and open the linked
   Additional Salary records from the form.
6. Generate or regenerate the Salary Slip covering Work Date.
7. Verify the overtime earning amounts and net pay before submitting.
8. Submit the Salary Slip; Settlement Status becomes `Paid`.

For a valid Cash adjustment approved before this release, the assigned approver
may use **Cash Settlement > Create Cash Settlement**. The same date and duplicate
guardrails run first. This action must not be used for a legacy multi-day record.

## Validation record

Local calculation-only validation completed on 2026-08-23:

- existing overtime reconciliation: 14 tests passed;
- cash-settlement calculations: 5 tests passed;
- retroactive date/deadline policy: 5 tests passed;
- mocked Frappe controller lifecycle: 6 tests passed in the installed DEV
  Frappe runtime;
- Python compilation: passed;
- DocType JSON parsing: passed;
- `git diff --check`: passed.

A read-only DEV compatibility calculation used Angel De La Rosa Lara's existing
submitted assignment `HR-SSA-24-12-00058` (DOP 136.38/hour). A hypothetical
10.0000 regular +35% hours plus 1.0967 night hours produced DOP 1,841.13 and
DOP 22.44 respectively, total DOP 1,863.57. No document was inserted or saved.

Full DEV transaction validation completed on 2026-08-23 against merged cash
settlement commit `9c01ccd1` plus the cancellation-guard correction described
below:

- Before state: Francis Florentino had no submitted Salary Structure Assignment
  covering July 2026, so cash settlement correctly stopped without creating a
  payroll input.
- Approved test setup: temporary submitted assignment `HR-SSA-26-08-00001`
  copied the existing `General Quincenal` structure with an explicitly approved
  test-only monthly base of DOP 22,908.00. The calculated hourly rate was DOP
  120.16.
- Exact transaction: same-day adjustment `OT-ADJ-2026-00002` covered 2026-07-20
  18:00–20:00, used existing Employee Checkins, and was capped at 2.0000 hours.
- After approval: the immutable result was 2.0000 regular +35% hours and DOP
  324.43. Submitted Additional Salary `SALADIC-26-08-00001` was created for
  `Horas Extras 35%` with that exact amount and source link.
- Payroll inclusion: draft Salary Slip `Sal Slip/None/00001` for 2026-07-16
  through 2026-07-31 contained base salary DOP 11,454.00 plus the exact DOP
  324.43 overtime row. Gross pay was DOP 11,778.43.
- Submission: submitting the Salary Slip changed the adjustment from `Created`
  to `Paid` and stored the Salary Slip reference.
- Rollback validation: cancelling the Salary Slip returned the adjustment to
  `Created` while preserving the submitted Additional Salary. Cancelling the
  source adjustment then cancelled the linked Additional Salary.
- Idempotency: a second cash-settlement attempt raised the expected validation
  error and did not create a duplicate payroll input.
- Cleanup: the temporary assignment, adjustment, Additional Salary, and Salary
  Slip are all cancelled. Francis has zero active temporary assignments, zero
  active 2026-07-20 test adjustments, and zero submitted linked test Additional
  Salary records.
- Control record: original `OT-ADJ-2026-00001` remained submitted and unchanged
  at 2.0000 verified hours, `Approved`, and `Pending` settlement.
- Scope: production and the Excel workbook were not changed.

### DEV-discovered direct-cancel guard correction

- Before state: cancelling a linked Additional Salary directly reached the
  intended hook, but the hook's second parameter was named `_`. Frappe passed
  the event method into that parameter, shadowing the translation function and
  raising `TypeError: 'str' object is not callable` instead of a controlled
  validation message.
- Exact application action: commit `c260273` renames the unused parameter to
  `method` and adds a regression test that invokes the hook with
  `before_cancel`.
- After state: direct cancellation raises the expected `ValidationError`
  instructing the operator to cancel the linked Retroactive Overtime Adjustment
  instead. The linked Additional Salary remains submitted.
- Validation: 7 controller lifecycle tests and 5 calculation tests passed in
  the DEV Frappe runtime; Python compilation and `git diff --check` also passed.
- Review status: correction is published in pull request #37. It must be merged
  and the resulting merge commit deployed before production rollout.
- Correction rollback: revert `c260273` and redeploy the prior merged commit
  `9c01ccd1`. No schema or payroll-record rollback is required for this code-only
  correction.

## Production replication

1. Merge the reviewed commit into `develop`.
2. In Frappe Cloud, deploy and update only the `igcaribe-bench` production bench.
   Let the normal deployment migration synchronize the new DocType fields.
3. Do not run a separate manual migrate, patch, or test suite on production.
4. Read back the PowerPro commit, site ping, DocType fields, and zero newly
   created overtime Additional Salary records immediately after deployment.
5. Cancel the invalid multi-day adjustment only after its draft Salary Slip is
   confirmed unsubmitted.
6. Create one corrected single-day controlled adjustment and inspect the cash
   preview before approval.
7. Approve it, verify the linked Additional Salary records, regenerate the
   draft Salary Slip, and reconcile hours × rate to the displayed amount.
8. Submit the Salary Slip only after operator approval.

## Rollback

If no Cash adjustment has been submitted after deployment, revert the release
commit and redeploy the previous PowerPro commit.

If settlement records exist:

1. cancel the related Salary Slip if submitted;
2. cancel the Retroactive Overtime Adjustment;
3. verify every linked Additional Salary is cancelled and absent from active
   payroll inputs;
4. then revert the release commit and redeploy;
5. read back payroll totals and settlement references.

Reverting code without cancelling active Additional Salary records does not
remove those payroll inputs; they must be reconciled first.

## Production risks

- Incorrect hourly rate from an outdated Salary Structure Assignment would
  affect only the approved adjustment being settled; the preview exposes the
  rate before approval.
- Missing or disabled overtime Salary Components block submission atomically.
- Existing draft Salary Slips do not automatically recalculate after a new
  Additional Salary record is created; regenerate or explicitly refresh them.
- Automatic processing is limited to new submitted Cash adjustments. There is
  no deployment-time historical backfill.
