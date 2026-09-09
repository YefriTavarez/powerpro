# Monthly employees in the second-quincena payroll

DGII Payroll Settings → Payroll Automation → **Include Monthly Employees in
Second-Quincena Payroll** (`include_monthly_in_second_quincena`) is an opt-in
checkbox, default off. It is a site-wide setting, as DGII Payroll Settings is a
Single DocType. Each Payroll Entry still scopes employees by its company.

When enabled, Get Employees on a Bimonthly entry beginning on the 15th or 16th
and ending on the last day of that same month includes both Monthly and Bimonthly
assignments. This matches the normal second-quincena use of `mid_month_start`;
the flag itself is a Salary Slip calculation field, so selection derives the
condition from the entry dates. A Monthly entry, first-quincena entry, timesheet
entry, partial closing period or cross-month period keeps its existing behavior.

For an August 16–31 entry:

| Employee assignment | Salary Slip frequency | Salary Slip period |
| --- | --- | --- |
| General Quincenal | Bimonthly | August 16–31 |
| General Mensual / General Iguala | Monthly | August 1–31 |

The usual Get Employees / payroll generation workflow runs both groups in one
entry. This setting does not schedule a job, submit Salary Slips automatically,
send bank payments or alter historical structures. The current submitted
assignment determines the structure and base; existing HRMS calculation handles
working days and components using each slip's own period. The payroll preview
shows the frequency and dates alongside each employee's amounts.

## Implementation and checks

- Resolve the latest submitted assignment within the entry company/currency and
  effective through period end, then verify its active submitted structure and
  payable account. Never fall back to a superseded assignment just because its
  frequency matches.
- Use the actual period for employee departure checks, attendance, withholding,
  readiness, additional-salary review and preview.
- Exclude employees with overlapping non-cancelled slips, including drafts and
  slips attached to other Payroll Entries. A first-quincena slip does not block
  a second-quincena slip, but it blocks a full-month slip for the same employee.
- Create both groups in one queued/synchronous transaction, with employee row
  locks, stale-job checks and one completion event. A repeated job reuses the
  exact same linked slip; conflicting slips cause rollback and an error.
- Submission/accrual and standard bank-entry reads include linked full-month
  slips while preserving their status, journal and Payroll Entry filters.
  Banco Popular batch already retrieves by Payroll Entry without a date filter.
- Existing linked monthly slips remain readable for processing after the setting
  is switched off. The saved Payroll Entry dates are never widened.

The adapter was reviewed against HRMS **v15.63.2** Payroll Entry / Salary Slip
source. Upstream changes to payroll creation, linked-slip reads, withholding,
attendance or job failure handling need compatibility review.

## Verification status

Local source is based on PowerPro `origin/develop` at `08ef054`. Run the isolated
suite (no site/database/network):

```sh
python scripts/test_mixed_frequency_unit.py
```

60 unit/controller-contract and existing monthly arithmetic regression tests
pass. Framework operations in this suite are test doubles; this does **not**
certify live HRMS integration or accounting. CI runs the same standalone suite.

Before production activation, on an explicitly authorized development site with
the deployed HRMS/Frappe versions and relevant customizations:

1. Keep the setting off and verify ordinary first- and second-quincena behavior.
2. Enable it. Use one active Monthly employee and one Bimonthly employee with
   submitted assignments and a month without existing slips. Check Get Employees
   and the preview, including a monthly employee's first-half attendance/leave.
3. Generate and compare the full-month employee's amounts/working days against a
   standalone Monthly calculation. Include joining/relieving dates, a changed
   base, Additional Salary, withholding and the company's deduction formulas.
4. Retry generation; check there are still only two linked slips. Test an existing
   draft/submitted overlap in another entry and a cancelled slip. Confirm queued
   and synchronous execution, including a cancelled/stale Payroll Entry.
5. Submit both slips and inspect balanced accrual entries, employer contributions,
   standard bank preview and Banco Popular batch amounts. Do not transmit money.
6. Turn the setting off with linked monthly slips still present. Confirm their
   submission/accounting/payment previews still include them.

No production schema, setting, payroll or payment was changed during development.
The live site/bench, installed app order and overrides must be rechecked before
deployment; old local copies are not proof of the current deployed controller.

## Deployment and rollback

Deploy through the normal reviewed Frappe Cloud release process and synchronize
the DGII Payroll Settings DocType. Keep the option off until the development
checks above pass and production activation is authorized.

To stop including new monthly employees, clear the checkbox and save, then
refresh an unprocessed draft entry's employee list. An in-flight mixed job whose
setting was disabled fails rather than silently changing frequency. Finish or
cancel any already-created mixed payroll through normal document workflows.
Do **not** remove this code while mixed entries still need processing: upstream
date filters would omit their full-month slips. No automatic cancellation,
recalculation or deletion is part of rollback.
