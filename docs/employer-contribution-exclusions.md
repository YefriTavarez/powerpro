# Salary structures excluded from employer contributions

In **DGII Payroll Settings → Exclusiones de aportes del empleador**, add Salary
Structures to **Estructuras salariales excluidas**. The migration adds
**General Iguala** once if that structure exists. Other structures can be added or
removed through the same list.

## Behavior

- Calculating a new Salary Slip or recalculating a draft records the exclusion in
  the read-only **Excluido de aportes del empleador** field and clears its employer
  contribution table. Both the monthly settlement and fallback calculation obey
  the list.
- Employee earnings, deductions, ISR, AFP/ARS withholding and net-pay formulas are
  unchanged. This setting controls employer contributions only.
- Monthly calculation snapshots also show an empty employer obligation list.
- Payroll Entry accepts an excluded slip with no employer rows and adds no
  employer expense/payable amounts for it. Mixed payrolls still accrue employer
  contributions for the other slips.
- Accounting reads the exclusion saved on submitted slips. Later setting changes
  do not reinterpret historical obligations. Existing submitted slips are not
  modified; existing drafts take the setting on their next recalculation/save.
- A slip marked excluded cannot contain dedicated contribution rows or nonzero
  legacy employer Salary Components. Legacy component pairs must be resolved in
  the Salary Structure before that slip can be saved; employee deductions are
  never silently removed.

## Development deployment and verification

Target: `/opt/erpnext/igcaribe-bench`, `igcaribe.fortabs.com` (Development).
Frappe 15.103.2, ERPNext 15.102.0, HRMS 15.58.5, PowerPRO 1.0.1.

The development deployment reloads only `Employer Contribution Exclusion` and
`DGII Payroll Settings`, then executes the reviewed installation function.
It does not need a full bench migration. The registered post-model-sync patch
installs the same field and initial setting through the normal release process.
The installer does not recalculate, submit or update existing Salary Slips.

The focused suite is run from the bench's `sites` directory (Development only):

```sh
../env/bin/python ../apps/powerpro/scripts/test_monthly_settlement_dev.py \
  --site igcaribe.fortabs.com --confirm-development
```

The runner blocks commits and email and rolls back its temporary payroll data.
Coverage includes an active temporary copy of the cancelled DEV General Iguala,
monthly closing, first-half payroll, draft recalculation, unchanged employee
amounts, submitted-slip history after settings changes, and mixed accounting.

## Rollback

Remove structures from the settings list to restore employer contributions on
future calculations. Recalculate any affected drafts. Keep the snapshot field
and accounting support for already-submitted excluded slips; removing the code
would make those slips fail the previous four-row accounting requirement.

Before any excluded slips have been submitted, the code can also be reverted and
the new metadata left in place as unused additive fields. Do not delete payroll
records or rewrite submitted slips as part of rollback.
