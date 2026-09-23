# HR Custom DocTypes and editable rules

Nineteen HR DocTypes are converted in place. Names, tables, fields, permissions and business rows are preserved. Existing definitions change only their `custom` flag. The original DocType directories are removed.

## Where the product owner edits behavior

There are 10 Client Scripts and 41 document-event Server Scripts, under `powerpro/custom_hr/client_scripts` and `powerpro/custom_hr/server_scripts`. The corresponding records in Desk are the runtime source of truth. An authorized Script Manager can edit them directly, including with AI assistance. The repository files are the release defaults.

Submitted-record immutability is checked in Before Save (Submitted Document), before post-save hooks can observe an invalid edit. Server Scripts own validations, approval/status assignments, draft resets, immutability and deletion guards, policy overlap rules, duplicate-claim checks, and editable messages. Client Scripts own form behavior. Event logic is no longer implemented in the 11 controller overrides. Five empty child types and three types needing only script guards use Frappe's `Document` directly.

Script names retain the `PowerPro HR v1 - ` prefix for stable identity; the installer manifest is version 2. Do not rename a script or change its DocType/event binding as a normal rule edit.

## Why Python remains

`override_doctype_class` selects capability classes through PowerPro's existing custom-controller loader. It is not evidence that the event rules remain in Python. None of the retained classes implements `validate`, submit/cancel events, update events, delete or rename guards. These methods are not whitelisted RPC endpoints.

| DocType | Remaining capability | Why it stays native |
| --- | --- | --- |
| Working Time Review / Incident | `is_service_write()` | Reads actual request flags; sandbox `frappe.flags` is a separate dictionary. |
| Overtime Rest Watch / Evidence Watch | `is_service_write()` | Same trusted service-state boundary. |
| Employee Supplement Revision | `is_internal_revision()` | Reads a private, identity-based authority token that client data cannot forge. |
| Employee Supplement Settings | `seed_supplement_history()` | Calls the existing atomic service using employee locks and private authority tokens. The settings validation is entirely in its script. |
| Ordinary Night Automation | `check_if_latest()`, `validate_policy()` | The employee mutex must precede Frappe's document snapshot; the worker needs an adapter to the editable policy function. |
| Ordinary Night Settlement | `check_if_latest()`, `build_night_preview()`, `validate_fresh_evidence()`, `create_night_earnings()`, `check_earnings_cancellable()`, `cancel_night_earnings()` | Early mutex plus imports of the existing evidence, freshness and payroll earning services. Scripts decide when to call them and assign derived fields/status. |
| Overtime Settlement Election | `is_managed_action()`, `evaluate_election(auth)` | Trusted request-action identity and the shared policy/evidence/entitlement service imports. Source selection, permission check and lifecycle state live in scripts. |
| Overtime Pay Policy | Shared capabilities only | No DocType-specific Python rule methods. |
| Solicitud de Dieta | `validate_new_request()` | Uses the existing locked and idempotent request service. CRUD guards live in scripts. |

The four night/policy/election classes share `current_roles()`, `locked_rows()` and `claim_digest()` from `HRScriptDocument`. These provide `get_roles`, bounded multi-row locking/current reads, and `hashlib`; those APIs/imports are unavailable in the safe namespace. Ordinary single-row locks use the sandbox's own `frappe.db.get_value(..., for_update=True)` directly in scripts.

Shared payroll calculation, evidence, accounting, permission and scheduler services remain app Python. This change does not turn the entire payroll engine into editable scripts. Changing an event rule cannot add an unsupported calculation algorithm to those services.

### Night worker policy contract

The **Ordinary Night Automation — Before Save** script exports `validate_policy(doc)`. Both the form and the night worker use this function. Keep it self-contained: use its `doc` argument, sandbox globals, and other top-level function definitions; do not rely on top-level assignments. The native worker adapter selects function definitions from this fixed enabled script and runs the exported function using Frappe `safe_exec`, with the same commit/rollback restrictions as document-event scripts. It does not run the form's draft/child-reset code, use unrestricted `exec`, or expose an API endpoint. Missing, disabled, rebound or invalid scripts fail closed.

## Editing and release upgrades

The installer uses a three-way comparison with the last installed upstream body fingerprint:

- Owner changed a script, release did not: preserve the owner's body.
- Release changed a script, owner did not: install the new body.
- Both changed it differently: stop before mutation and report the script requiring an explicit merge.
- Same final body: accept it. Missing records are recreated from defaults.

Existing enable/disable choices are preserved. Disabling a guard changes system behavior, just as editing its body does; the installer does not silently re-enable it. Script identity, metadata drift, additional scoped customizations and unreviewed outbound event bindings remain preflight conflicts. Conflicting merges should be prepared against the previous release, then explicitly reviewed/applied to the release defaults and/or site record so the next preview is clean.

Only upstream fingerprints are stored transactionally in a scoped `DefaultValue`; full before-images stay in the site's private backups. Version-1 fingerprints support upgrading already converted sites. Repeated installation does not resave unchanged or owner-edited scripts. Owner changes are not silently exported to git or other sites.

## Rollout and recovery

Use `powerpro.custom_hr.installer.preview` for a read-only preflight. Server Scripts must be enabled. The pre-model-sync patch and `before_migrate` hook install the scoped metadata/scripts; `after_install` creates absent definitions on fresh sites. The installer does not commit the caller's transaction.

Confirm the database identity of every site sharing the checkout, back up SQL/configuration, pause all writers, and refresh metadata, controller/script caches and application processes after conversion. Site aliases can share one database. Existing notifications/webhooks run before Server Scripts in Frappe's event pipeline; the installer blocks enabled scoped bindings pending review. Audit resolved `doc_events` as part of target preflight too.

Version 2 keeps `powerpro-hr-custom-v2-before.json`, leaving the original version-1 checkpoint intact. With writers paused and the installer still available, run `rollback`, commit only on success, restore the source matching that before-image, and refresh caches/processes before reopening. The inverse restores original custom flags, previous script bodies/enablement and upstream fingerprints. It removes only unchanged script metadata records created by this release, so reapply recreates required guards enabled. It refuses intervening metadata/script changes and destructive fresh-schema deletion. Restore-based recovery requires a separately verified checkpoint and reconciliation of newer business activity.

## Validation

Use `scripts/test_hr_custom_dev.py` only on an isolated Development site with `developer_mode` and `powerpro_hr_rehearsal`. It blocks commits, email and jobs and rolls back its fixtures. Coverage includes controller resolution, real document-event guards, owner edits reaching both form and worker, sandbox/import restrictions, idempotency, three-way conflicts, identity/enablement, and inverse/reapply.

Test on the target Frappe version, not just with Python compilation: Frappe 15.103.2 lacks the restricted tuple-assignment helper, forbids `str.format`, exposes `as_json` globally, and requires `json.loads` instead of `frappe.parse_json`. Integration coverage must exercise native night settlement/automation, concurrency, supplements, dietas, review/incident and rest/evidence workflows. Fresh-install checks certify metadata/controller/script compatibility, not every payroll feature's business setup.
