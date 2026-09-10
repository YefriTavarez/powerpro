# Manual verification of completed overtime attendance

Status: implemented in a local development branch; not deployed or enabled on any site.

## Target and evidence

The source baseline is PowerPro `1ec7dede9137cdf9767ea35105afd8d56eb5192e`, read from `/opt/erpnext/igcaribe-bench` on `igcaribe.fortabs.com` on September 10, 2026. Frappe 15.103.2, ERPNext 15.102.0, HRMS 15.58.5, PowerPro 1.0.1. Other installed apps: Print Designer, Wiki, Drive, Survey Pro, Nubef and Quality Traceability. The configured default site is `igcaribe.local`; always specify the target site. The inspected site is treated as production.

Live inspection found no site-level custom fields, property setters, client/server scripts or workflows on the two overtime DocTypes. PowerPro's Dieta hooks are installed and can flag paid dietas for attendance review. DGII Payroll Settings has separate monthly-settlement custom fields, which this change does not alter. Its existing settlement roles are `Encargado de Gestión Humana` and `System Manager`; that list is not changed or automatically copied.

The existing attendance reconciliation derives hours from Employee Checkins. A saved snapshot in Completed, Partial or Overrun with positive verified hours is required by settlement. The new action supplies explicit manager-certified worked intervals to the same hour-classification rules without inserting or altering any Employee Checkin.

## Configuration and operator flow

In **DGII Payroll Settings → Manual Overtime Attendance Verification**:

1. Configure **Manual Overtime Verification Roles**, one existing, enabled Desk role per line.
2. Enable **Enable Manual Overtime Verification** when the rollout is approved. Default: disabled; role list: empty.

Every preview and confirmation reads this configuration on the server. There is no Administrator/System Manager bypass. Users also need document read/write permission on the authorization and, when linked, the Work Call. Verification and settlement permissions remain independent. A custom role may need the usual Role Permission Manager configuration; adding it to this list alone does not grant broader document access.

On a submitted Work Call, choose **Overtime → Manually Verify Attendance** (Spanish: **Verificar asistencia manualmente**). Select an employee/date whose authorized window has finished. Enter actual intervals, excluding breaks, and explain the evidence used or the reason for missing/incorrect check-ins. Supporting documents can use the existing attachment facility on the Work Call or authorization.

Review verified hours, real check-in hours, the difference, warnings, overtime categories and outside-window hours. **Approve Attendance** persists the attendance evidence and updates the team's totals. It does not create Additional Salary, Leave Allocation, compensatory credit, or any payment. Use the existing individual or team settlement preview afterward. The individual authorization form exposes the same action, including for standalone authorizations.

Each approval applies to the selected employee/date. The existing team settlement still requires every included authorization to be eligible; future, absent or otherwise unresolved colleagues must be handled separately, or eligible authorizations can use individual settlement.

## Validation and audit

- Server-side feature, role, document-permission, submitted/approved-state and settlement-state checks.
- No certification before the approved window ends, including for System Manager.
- One to 24 nonoverlapping intervals, valid local datetimes, no future end, each overlapping the authorized window. Zero eligible overtime is rejected.
- Existing regular-shift exclusion, authorized-window clipping, maximum-hour limit, weekly 35%/100% split, holiday, weekly-rest and night rules remain in use.
- Verify regular overtime in chronological order. Certification that could alter the split of later verified regular overtime in the same week is blocked for reconciliation review.
- Confirmation recalculates the preview and rejects stale inputs or changed evidence/settings. The live database uses REPEATABLE READ. Confirmation uses current locking reads for the source, settings, schedule, check-ins, weekly history and team totals rather than an earlier consistent-read snapshot. Real MariaDB concurrency still needs staging validation.
- The saved snapshot records source, reason, raw worked intervals, real check-in comparison, verifier and timestamp. Comments retain before/after snapshots when correcting an unsettled verification.
- Normal document-save APIs cannot forge the manual fields or edit a certified snapshot. Authorized amendments use a new preview and reason; settled/cancelled sources cannot be amended.
- Work Call check-in refresh preserves manual snapshots. Standalone check-in saves refuse to overwrite them. Later weekly calculations count certified regular hours.
- Snapshot, Dieta on-change hooks, team totals and audit comments are part of the same request transaction; no explicit commit is introduced.

## Local validation

✅ Run from the local custom-app checkout:

```sh
python3 tests/run_overtime_checks.py
node --test tests/test_manual_overtime_ui.cjs
```

113 Python checks pass: 37 new service/rule tests with an in-memory Frappe adapter, 22 existing settlement controller checks, and 54 existing pure overtime checks. Nine UI interaction tests pass. The `es-DO.csv` symlink now uses the relative `es.csv` target so these Spanish translations work across bench paths. Python compilation, JavaScript syntax and diff whitespace are also checked.

The adapter exercises actual service and classifier code, but is not a Frappe integration environment. It does not certify MariaDB locking/rollback, effective user permissions, installed Dieta hooks, or actual Frappe dialog rendering.

## Required isolated integration rehearsal

Before deployment, use a confirmed disposable development bench or explicitly approved isolated staging copy, with outbound effects muted. Do not run Frappe test runners on production.

Verify:

1. Metadata reload preserves existing DGII settings/custom fields; feature remains disabled and role list empty.
2. An ordinary unauthorized role and Administrator without a listed role are denied through direct API calls. A listed role with the required document permissions succeeds. Revoking the role after preview blocks confirmation.
3. Completed weekly-rest work with no punches can be certified for compensatory rest; future work cannot. Preview/save do not create payroll/leave/payment records or synthetic punches.
4. Breaks, partial attendance, out-of-window time, overnight work, regular weekly thresholds, holiday and night categories agree with the preview.
5. Changing check-ins, settings or the authorization between preview and save forces a new preview. Repeated confirmation creates no duplicate audit/credit.
6. Concurrent manual approvals, check-in refresh, cancellation, Dieta payout and settlement preserve source state and totals. Inject a failure after the snapshot write and verify transaction rollback includes Dieta effects and comments.
7. Paid Solicitud de Dieta records receive the existing attendance-review flag for Partial/Overrun when applicable; this action itself pays nothing.
8. Manual snapshots survive later check-in refresh. The separate settlement workflow still creates the appropriate single audited output and blocks duplicate settlement.
9. Spanish dialogs render correctly in Frappe, including selection changes, interval table editing, preview, correction and approval.

## Scoped rollout plan — not executed

Record the authorized target, commit, installed apps, environment and backup before any site-changing command. Recheck source drift before applying the patch. Apply it to the reviewed custom-app branch; no core-app files are modified.

✅ On the approved target, take the normal verified database/files backup and export the two current overtime role/enable settings for rollback. The commands below deliberately use the explicitly selected site; they are a plan, not evidence of deployment.

⚠️ Once the reviewed code is installed, reload only the two modified DocTypes using the site's working helper:

```sh
cd /opt/erpnext/igcaribe-bench/sites
../env/bin/python -m frappe.utils.bench_helper frappe --site igcaribe.fortabs.com reload-doctype "DGII Payroll Settings"
../env/bin/python -m frappe.utils.bench_helper frappe --site igcaribe.fortabs.com reload-doctype "Overtime Authorization"
../env/bin/python -m frappe.utils.bench_helper frappe --site igcaribe.fortabs.com clear-cache
```

⚠️ Restart only the approved bench's web/workers through its established process manager to load new Python. Confirm any brief service interruption in the rollout scope. The new JavaScript is loaded through `frappe.require` from the existing app assets path; verify that file is served before enabling. No full migrate, patch runner, production test runner or core edit is part of this plan.

✅ Read back live field metadata, permissions, disabled flag, role list, deployed commit and static asset. Verify the baseline authorization and business-document counts are unchanged.

⚠️ After the integration rehearsal and rollout approval, configure the desired roles in DGII Payroll Settings and enable the feature. Confirm with one completed, unsettled record before wider use. The September 13 authorization from the investigation remains future work on September 10 and is not a valid pilot.

## Rollback and production risks

The immediate reversible rollback is to uncheck **Enable Manual Overtime Verification** in DGII Payroll Settings and read it back as disabled. New manual previews/approvals are denied immediately; existing evidence remains intact. Do not drop the new fields or remove the preservation logic after records have been manually verified. Reverting to old code after use could allow a check-in refresh to overwrite certified evidence. A complete code rollback therefore requires a separate record-by-record plan, keeping the snapshot-preservation protections until all affected records are resolved.

Verification does not reverse or cancel a settlement. Any already-created payroll or leave output follows its existing approved cancellation process.

Main blast radius: selected authorization attendance, its Work Call totals, and existing linked Dieta attendance-review flags. These hours can later affect cash or compensatory leave when settlement is confirmed. Outstanding risks are the real-site integration/concurrency cases above and operational evidence quality, not a reason to bypass the server validations.
