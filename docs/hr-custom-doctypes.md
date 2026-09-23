# HR Custom DocType migration

The migration converts 19 PowerPro HR DocTypes in place. It preserves names, tables, fields, permissions and business rows; existing definitions change only their custom flag.

## Runtime layout

- Nineteen JSON definitions: powerpro/custom_hr/definitions.
- Ten form Client Scripts: powerpro/custom_hr/client_scripts.
- Seven document-event Server Scripts replace the guards for Overtime Reconciliation Run, Overtime Attendance Exception and Lote de Pago de Dietas.
- Eleven controllers remain ordinary Python under powerpro/controllers/hr_custom because they depend on controller methods, locks, trusted services or authority checks outside the Server Script sandbox.
- Five empty child controllers use Document.

PowerPro's existing custom-controller loader remains in use. Request and job initialization hooks discard stale scoped controller classes. Shared payroll, evidence, permission, accounting and scheduler services remain app Python.

## Upgrade and fresh install

Server Scripts must be enabled before installation. The pre-model-sync patch and before_migrate hook run the scoped installer before obsolete standard definitions can be removed. The after_install hook creates missing definitions on fresh sites. Existing supplement/employer-exclusion setup patches use the same installer.

Use powerpro.custom_hr.installer.preview for a read-only preflight. The installer rejects unreviewed metadata changes, scoped customizations, conflicting scripts and outbound event bindings requiring review. It keeps a private original before-image and is idempotent. It does not commit the caller's transaction.

Before rollout, confirm the database identity of every site sharing the checkout, not just each site-directory name. Site aliases can use the same database. Back up SQL and configuration, pause writers through all aliases, then refresh metadata, controller and script caches and application processes after conversion.

## Rollback

Retain matching baseline source and the installer before-image. With writers paused, call powerpro.custom_hr.installer.rollback in the converted site's framework session, commit only on success, restore baseline source, and refresh caches/processes before reopening. Keep the installer available until the inverse is complete.

The inverse restores original custom flags and prior script enablement, and refuses metadata/script drift or destructive fresh-install deletion. Reconcile intervening business activity before rollback. A database restore can overwrite newer transactions and is not an automatic inverse.

## Verification

The implementation was verified on isolated Development databases with the installed Frappe 15.103.2 / ERPNext 15.102.0 / HRMS 15.58.5 stack:

- Full upgrade migrations, repeat installation, empty-site installation and first migration.
- Eleven focused migration tests on upgraded and fresh databases; inverse/reapply checks and unique-index verification.
- Unchanged retained-controller syntax trees and moved JSON/JavaScript contents.
- Supplement and dieta integration, permission and guard behavior, UI tests, and representative browser form checks.
- Night concurrency, review/incident, evidence-monitor and compensatory-rest workflows.
- Independent metadata and business-data integrity readback after Development conversion.

The acceptance fixture changes account for populated databases, fixed historical approval dates, a copied special Friday shift end, and the existing cancelled-document list filter. They do not weaken application rules.

scripts/test_hr_custom_dev.py requires developer_mode and the dedicated powerpro_hr_rehearsal flag. It rejects commits and outbound email/jobs and rolls back its fixture writes. Do not run acceptance fixtures on production. Fresh-install checks certify metadata/controller/script compatibility, not every payroll feature's initial business configuration.
