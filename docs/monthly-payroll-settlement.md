# Monthly payroll settlement — PowerPro v1

## Behavior

The feature is opt-in in DGII Payroll Settings, scoped to installed Salary Structures,
and effective from the first day of a month. `General Quincenal` is the initial DEV
target. Installation changes neither submitted slips nor drafts already stored.

The source of truth is actual `Salary Detail.amount` after HRMS payment-day adjustment:
confirmed earlier slips of the employee/company/month plus the current slip. B is
salary paid in the period; BAM and the current Assignment.base are never summed as
actual monthly income. Multiple Additional Salary rows are summed once from the slip.
The current COM abbreviation retains its original meaning.

The controller prepares the monthly context between earnings and deductions, injects
`pp_*` values into both HRMS formula dictionaries, and exposes the pure ISR calculator
through `pp_isr(DP)`. Managed monthly deduction rows use no second payment-day proration.
The private structure copy prevents changing the globally cached structure. When the
feature is disabled, stored original formulas and proration semantics still apply.

The month is the salary period, not posting/creation date. Ordinary Monthly/Bimonthly
slips ending on the final calendar day settle the month. Earlier slips expose an
informational accumulation and apply no AFP, ARS, ISR or employer monthly amounts.
Dependents, transport, loans and their existing timing rules are unchanged.

Employee and employer AFP/ARS use B + COM + VAC, with their respective date-effective
ceilings. ISR retains B + COM + VAC + BVA + INC + BNF + HRE + HN + HE and also includes
new earning components marked **Is Tax Applicable** (for example ORC), less monthly
employee AFP/ARS and dependents. The flag and amount come from each current or prior
submitted Salary Detail row, not the current component master. Statistical rows are
excluded; multiple Additional Salary rows are counted once each. Original known
abbreviations retain their classification for compatibility with historical rows.
INFOTEP uses B + COM; SRL uses B + COM + VAC with its ceiling. Marking a new component
taxable adds it to ISR only; it does not classify it as salary, commission or vacation
for contributions. Such a change requires a separate business rule.
Each obligation subtracts previously recorded amounts. Negative differences block
submission rather than creating an automatic refund. Mixed currencies or employer
accounting modes also block. ISR must have a verified
scale for the closing year; the current version supports the existing 2025/2026 scales.

## Integrity and visible evidence

Submission locks the Employee row until transaction completion, recalculates using
locking/current reads, and revalidates previous period coverage. Draft or cancelled
slips do not satisfy coverage. Employment start limits the coverage requirement.
Overlaps, later submitted slips, cross-month periods, unsupported frequencies, and
early departures block ordinary settlement. Cancellation checks saved dependencies
even after feature deactivation. A second ordinary close is rejected; post-close
corrections require an explicit cancellation/amendment workflow.

`Salary Slip.monthly_settlement_snapshot` records inputs, source slips and rows,
rules, bases, obligations, previous amounts, applied amounts and issues. The new
Acumulado mensual tab renders it. Employer Contribution Detail retains the four
existing rows and accounts. Payroll Entry previews read this table and compare the
new calculation against the legacy calculation in memory, without saving slips.

The existing salary-to-ledger integration consumes the persisted employer amounts,
with balanced expense/payable entries and no employer deduction from employee net.

Snapshot version 2 also records `current_taxable` and `previous_taxable` amounts by
abbreviation. New-component support uses the existing activation and effective date;
it requires only a code deployment, not an installer rerun or formula rewrite. If a
user edited a guarded formula after installation (for example adding ORC to the legacy
branch), preserve that edit. The original installer's drift checks intentionally reject
reinstall/rollback over changed formulas; reconcile such edits explicitly before using
those operations. Submitted evidence and existing slips are never rewritten by this change.

## Explicit DEV installation

Confirmed target: `/opt/erpnext/igcaribe-bench`, site `igcaribe.fortabs.com`, DEV.
Frappe 15.103.2, ERPNext 15.102.0, HRMS 15.58.5. Always specify the site because
the bench default is `igcaribe.local`.

From `/opt/erpnext/igcaribe-bench/sites`:

✅ Read-only installer status:
```sh
../env/bin/python -m frappe.utils.bench_helper frappe --site igcaribe.fortabs.com execute powerpro.patches.v1.setup_monthly_settlement.preview
```

⚠️ Install fields and guarded formulas, initially disabled. Original component and
structure-row settings are retained in a hidden JSON backup before formula changes.
This is deliberately not an automatic migration patch. The installer rejects drift.
```sh
../env/bin/python -m frappe.utils.bench_helper frappe --site igcaribe.fortabs.com execute powerpro.patches.v1.setup_monthly_settlement.execute
```

⚠️ DEV-only tests: create labelled fixtures inside a transaction, forbid commits and
outgoing email, and roll back on completion. Never run this command on production.
```sh
../env/bin/python ../apps/powerpro/scripts/test_monthly_settlement_dev.py --site igcaribe.fortabs.com --confirm-development
```

⚠️ Explicit DEV activation, September 2026:
```sh
../env/bin/python -m frappe.utils.bench_helper frappe --site igcaribe.fortabs.com execute powerpro.patches.v1.setup_monthly_settlement.enable --kwargs '{"from_date":"2026-09-01"}'
```

⚠️ Restore exact original formulas/settings while keeping audit fields and submitted evidence:
```sh
../env/bin/python -m frappe.utils.bench_helper frappe --site igcaribe.fortabs.com execute powerpro.patches.v1.setup_monthly_settlement.rollback
```

Rollback does not reverse payroll or GL entries. Reload application processes only
after checking the relevant queues; do not restart unrelated benches. When reverting
code after new slips have been submitted, retain the dependency-protection code until
those records have been reviewed. The database backup is a disaster-recovery fallback,
not the routine rollback mechanism.

## Production handoff

Production `igcaribe.com` is a separate deployment, not authorized by the DEV rollout.
First discover its actual bench, installed app versions/order, hooks, customizations,
formulas and employer mode. Compare them with the DEV evidence and refuse a blind
copy of this site's formula backup. Create a production backup, install disabled,
preview the proposed closing payroll against confirmed prior slips, and agree the
effective month before enabling. Any necessary production migration is user-run.
No existing slip, Additional Salary, assignment, journal or bank batch is automatically
recalculated, submitted, cancelled, posted or paid by the installer.
