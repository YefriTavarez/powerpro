# IGC employer contribution journal

## Objective

Keep employer AFP, ARS, INFOTEP, and SRL outside the employee-facing Earnings and Deductions tables while preserving balanced payroll accrual accounting.

This implementation is feature-gated. `Salary Component Pairs` is the safe deployment default. `Dedicated Journal Entries` is enabled only after site validation.

## Target context validated on DEV

- Bench: `/opt/erpnext/igcaribe-bench`
- Site: `igcaribe.fortabs.com`
- Environment: development
- Frappe: 15.103.2
- ERPNext: 15.102.0
- HRMS: 15.58.5
- PowerPro: 1.0.1
- PowerPro already overrides Salary Slip and Payroll Entry; no competing Server Script or Workflow was found on either DocType.

## Before state

Eight excluded Salary Components produced four balanced pairs:

- Gasto AFP Empleador / AFP Empleador
- Gasto ARS Empleador / ARS Empleador
- Gasto INFOTEP Empleador / INFOTEP Empleador
- Gasto SRL Empleador / SRL Empleador

`Do Not Include in Total` protected employee gross/net totals, but HRMS still displayed the rows in Earnings and Deductions and used them to create the accrual Journal Entry.

## After state

In dedicated mode:

1. Salary Slip stores four immutable child snapshots in `Employer Contribution Detail`.
2. Legacy employer Salary Component conditions evaluate false, so no employer rows appear in employee Earnings or Deductions.
3. The PowerPro Payroll Entry override appends equal debit and credit lines to the standard accrual Journal Entry.
4. Employee payroll payable remains unchanged because the appended employer entries net to zero.
5. A payroll mixing legacy and dedicated slips, or a dedicated slip containing legacy employer rows, is rejected before posting.

The snapshot records code, cotizable base, rate, ceiling, amount, expense account, liability account, and rule effective date.

## Rules

| Contribution | Base | Rate | Expense | Liability |
| --- | --- | ---: | --- | --- |
| AFP employer | Monthly assigned salary | 7.10% | 612101 | 213108 |
| ARS employer | Monthly assigned salary | 7.09% | 612101 | 213108 |
| INFOTEP employer | Monthly salary + commissions | Configured, currently 1.00% | 612401 | 213109 |
| SRL employer | Monthly salary + commissions + statutory vacation, capped by the effective SRL ceiling | Configured, currently 1.20% | 612201 | 213108 |

For bi-monthly payroll, employer contributions are settled on the second half. The first half contains no employer snapshot. Monthly payroll settles in its single slip.

Commissions and statutory vacation from a prior submitted first-half slip are included in the second-half monthly base. Current-slip Additional Salary rows are included directly.

## DEV change log

### Change 1: data model and feature gate

- Before: no dedicated employer contribution child table or accounting mode.
- Action: reload app-owned `Employer Contribution Detail` and `DGII Payroll Settings`; execute `powerpro.patches.v1.setup_dedicated_employer_contribution_journal.execute`.
- After: three Salary Slip custom fields exist; settings defaulted to `Salary Component Pairs`; all eight legacy conditions became feature-gated.
- Validation: patch readback reported all fields and all eight gated conditions; zero submitted Salary Slips changed.
- Rollback: execute `powerpro.patches.v1.setup_dedicated_employer_contribution_journal.rollback`.

### Change 2: Salary Slip snapshots

- Before: employer obligations existed only as excluded Earnings/Deductions.
- Action: PowerPro Salary Slip sets settings before formula evaluation and populates the dedicated child table after core net-pay calculation.
- After: Ceily second-half calculation stored AFP 3,550; ARS 3,545; INFOTEP 500; SRL 600 on a 50,000 salary, without legacy employer rows.
- Validation: legacy and dedicated gross, deductions, and net pay were identical; first-half dedicated calculation stored no employer rows; Salary Slip record count remained unchanged during the unsaved comparison.
- Rollback: switch settings to `Salary Component Pairs`; existing submitted snapshots remain historical evidence and are not recalculated.

### Change 3: Payroll Entry accrual Journal Entry

- Before: HRMS derived employer debit/credit lines from paired Salary Components.
- Action: PowerPro calls the installed HRMS v15.58.5 method first, then appends equal employer expense debits and liability credits from submitted Salary Slip snapshots.
- After: a controlled Ceily payroll with a 1,000 commission created a balanced 34,217 accrual Journal Entry. Employer snapshots totalled 8,217; expense debits were 8,217; shared TSS/INFOTEP liability credits reconciled to 8,217 employer plus 2,955 employee AFP/ARS.
- Validation: standard accounting and employee-wise accounting variants both passed. Six test-harness Payroll Entries remain canceled (`NOMI-2026081800001` through `00006`); all test Salary Slips and Additional Salary records were removed; four balanced Journal Entries (`ACC-JV-2026-00003` through `00006`) remain canceled for audit.
- Rollback: cancel any affected draft/test payroll, execute the rollback method, and regenerate only unsubmitted Salary Slips in legacy mode. Never rewrite submitted historical payroll.

### Change 4: rollback drill

- Before: DEV was in dedicated mode after testing.
- Action: execute rollback, validate legacy settings and conditions, reapply setup, then explicitly enable dedicated mode.
- After: DEV returned to `Dedicated Journal Entries` with gated legacy conditions.
- Validation: both modes and exact condition strings were read back after each transition.

## Production replication

1. Confirm production versions, installed apps, resolved overrides, custom fields/scripts/workflows, and current draft payroll count.
2. Take a production backup through Frappe Cloud.
3. Deploy the reviewed PowerPro commit through Frappe Cloud `Deploy and Update`. The migration creates the app DocType and runs the idempotent patch in legacy mode.
4. Read back the new fields, eight gated legacy conditions, and `Salary Component Pairs` setting. Confirm submitted Salary Slip counts and amounts did not change.
5. Ensure no in-progress payroll mixes old draft slips with newly generated slips. Finish the old payroll in legacy mode or cancel/regenerate only its drafts.
6. Generate an unsaved or controlled second-half Salary Slip and compare gross, employee deductions, net pay, and the four snapshots.
7. Set `DGII Payroll Settings.employer_contribution_mode` to `Dedicated Journal Entries` using the native Frappe API.
8. Generate and submit one controlled Payroll Entry, read back the Salary Slip and Journal Entry, and reconcile debits/credits before normal payroll use.

## Production rollback

1. Stop creation/submission of new payroll entries.
2. Cancel any affected unsubmitted or controlled payroll entry.
3. Set the mode to `Salary Component Pairs`.
4. Restore the legacy conditions with the patch rollback method during an approved maintenance action, or deploy a rollback commit that invokes the same idempotent logic.
5. Regenerate only draft Salary Slips.
6. Verify employee net pay and the accrual Journal Entry before resuming.

Do not cancel, amend, or recalculate submitted historical payroll merely to change accounting mode.

## Risks and controls

- Mixed modes: blocked before Journal Entry creation.
- Double posting: dedicated slips containing legacy employer rows are blocked.
- Missing snapshots: a second-half/monthly dedicated slip must contain exactly four rows.
- Account or negative-amount errors: blocked on Salary Slip validation.
- Draft drift after a settings change: each Salary Slip snapshots its mode; production cutover must account for existing drafts.
- Version drift: the override signature is validated against HRMS 15.58.5 and should be rechecked before upgrading HRMS.
- Monthly live test: DEV has only the active `General Quincenal` / `Bimonthly` structure. Monthly branching is implemented and covered by the same calculation path, but a live monthly Salary Slip cannot be generated until an active monthly structure exists.
