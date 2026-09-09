# Solicitud de Dieta

PowerPro's Work Call is the operational screen. On an authorized date marked
**Permite dieta**, an assigned Expense Approver or HR Manager can select workers,
change amounts, approve and record daily payments entirely through modals.
An employee request is optional; `/dietas` lets employees request for themselves.
The manager reuses that record when paying. Payroll settlement is untouched.

## Implementation

- Company defaults and payment mappings are child tables in IGC Settings.
- Solicitud de Dieta is uniquely keyed by company/employee/work date. Its audit
  records initiation, amount snapshots, decisions, payment and corrections.
- Lote de Pago de Dietas contains full payments for selected workers from one
  call/date/payment source, an idempotency key and accounting snapshots.
- REST writes to the operational DocTypes are denied. Validated POST actions own
  creation and modification. Read/query hooks enforce employee/approver scope.
- Work Call / Employee locks plus the unique daily key serialize payouts across
  callers. Preview versions include source, employee, configuration and request
  state. Confirmation rechecks all rows before any insert. A savepoint makes
  batches atomic even if an internal Python caller catches the error.
- After commit, the internal generator locks the batch, creates a draft Journal
  Entry and stores its link in the same transaction. Payouts survive a queue or
  accounting failure. Operator retry never repeats a payout. The generator never
  submits a JE and accepts no arbitrary accounts or amounts from the browser.
- A confirmed payout is a record of money already delivered, not a bank transfer.
  JE status and approval status are independent of actual payout status.
- Cancellation/attendance hooks preserve paid history and flag HR review. A
  whole-batch clerical correction requires HR Manager, a reason and Finance
  cancellation of any linked JE. It does not record an actual refund.

## API contract

All endpoints are under `powerpro.dietas.service` unless specified otherwise.

| Endpoint | Input | Result |
|---|---|---|
| `work_call_context` | Work Call, optional work date | scoped workers with versions, dates, methods and summary |
| `preview_payout` | Work Call/date, selected employee+amount+version+reason rows, payment date/method/reference/evidence | server preview and token |
| `confirm_payout` (POST) | same input, token, UUID idempotency key | confirmed batch and accounting state |
| `manage_requests` (POST) | Work Call/date, versioned rows, action and reason | changed request count |
| `payment_history` | Work Call | scoped batches, details and audit |
| `my_dietas` | none | current employee's requests and eligible authorization summaries |
| `request_dieta` (POST) | eligible authorization, optional notes | created/reused request |
| `powerpro.dietas.accounting.retry_accounting` (POST) | batch name | queues the internal draft generator |
| `powerpro.dietas.accounting.reverse_erroneous_payout` (POST) | batch name and reason | audited clerical correction |

The API never expands the operator's existing Work Call read permission. Before
activation, verify that intended operators can already read the relevant Work
Call and that employee/company User Permissions match their intended scope.
HR authority alone does not override explicit Company/Employee/Department User
Permissions. Employees never receive full Work Call documents through self-service.

## Local verification

✅ These tests use local adapters and DOM fixtures; they do not connect to a site:

```sh
python3 tests/test_dietas.py
npm ci --prefix tests
node --test tests/test_dietas_ui.cjs
node --check powerpro/public/js/dietas.js
```

Use Node 22.22.2+ for the jsdom test dependency. The Python adapter exercises real
service functions, persistence failure rollback, stale previews and accounting
retry paths. It is not proof of MariaDB isolation or live Frappe rendering.

## Production preflight and release gates

Implementation was based on upstream develop `08ef054`. Read-only UI inspection
confirmed Overtime Work Call is installed at igcaribe.com and its list was empty
in that session. Production SSH returned `Permission denied (publickey)`; the
full live app order, versions, effective customizations and hooks were **not
verified**. The source-only checkout has no bench/site/database attached.

Before installation, establish the live bench path, internal site name, default
site, environment, versions, app resolution order and all effective customizations.
The known historical mapping `/home/frappe/frappe-bench` / `igcaribe.erpnext.com`
must be rechecked. Do not use the separate nubef.local checkout as live evidence.

✅ Read the source of `powerpro.dietas.preflight.inspect` first. It performs only
selective reads and excludes config secrets. In a read-only bench console:

```python
from powerpro.dietas.preflight import inspect
result = inspect()
print(frappe.as_json(result))
```

Before this branch is present, perform those same read-only queries manually.
Review relevant custom scripts' source, wildcard hooks, controller overrides and
any mandatory accounting dimensions before approving deployment. Inspect account
and cost-center validity, employee/user/Expense Approver assignments, permissions,
and Work Call feature settings. Configure missing business values explicitly;
no production allowance amount or account IDs are hardcoded by this change.

✅ Develop on an isolated development site with Frappe/ERPNext/HRMS v15 and
PowerPro. Use the guarded rollback-only runner (replace paths with the verified development bench):

```sh
env/bin/python apps/powerpro/scripts/test_dietas_dev.py --site VERIFIED_DEV_SITE --sites-path /VERIFIED_DEV_BENCH/sites --confirm-development
```

It refuses the known production site/hostname and prohibits commits and email.
These three DB tests are also wired into the existing CI disposable `test_site`;
that CI run has not been executed from this local task.
⚠️ Run a staging pilot only after explicit staging authorization.
🚨 Production schema synchronization and migration remain user-run, after a
reviewed backup/rollback plan. The following are templates, not executed commands:

```sh
bench --site VERIFIED_SITE backup --with-files
bench --site VERIFIED_SITE migrate
bench build --app powerpro
```

Backup is ✅ read-only with respect to business records. Migration is 🚨 because it
runs all pending patches/schema synchronization, not just dietas. Build is ⚠️ and
may require the host's normal app/asset deployment mechanism. Never run production
bench tests or use this document to authorize a production update implicitly.

After schema sync, keep the feature disabled. Configure one company row, positive
amount, allowed payment methods, and (if desired) expense/cash/bank accounts and
cost center. JE generation defaults off. Existing dates remain unmarked.

Pilot with an explicitly approved small group and new authorized Work Call dates.
Verify manager and employee identities, readback of defaults, and all three modal
buttons without navigation. Register only actual separately authorized payouts.
When accounting is enabled, verify batch total = JE debit = JE credit, draft
status, worker details, Finance submission and ledger readback. Daily review:
unpaid requests, confirmed payout totals, accounting errors and HR review flags.

### Staging acceptance still required

- Two DB sessions paying the same employee/date; one winner, no duplicate record.
- Two sessions with different Work Calls and a common employee/date.
- Cancel a source between preview and confirm; no payout persists.
- Simulate response loss after commit; same-key retry returns the original batch.
- All-or-nothing rollback on a middle-row write failure.
- Real Work Call controls, Attach field, Select options and mobile employee page.
- Draft JE generation with actual company accounts/dimensions, queue outage,
  retries, submission, cancellation and HR correction.
- Verify no Salary Slip, Additional Salary, Expense Claim or Employee Advance.

## Rollback

Disable `enabled` for the company in IGC Settings, retaining rows/defaults and
payment mappings. New requests/payments stop; history remains accessible from
Work Calls, employee self-service and the stored records. Resolve confirmed
batches' accounting using their original snapshots; changing configuration does
not rewrite them. Do not delete schemas, payout rows, requests or audit logs.
Finance handles any JE corrections through normal cancellation/reversal rules.
Reverting the application commit alone is not a financial rollback.
