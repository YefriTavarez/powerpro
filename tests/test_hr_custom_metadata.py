"""Integration regression tests; run only through test_hr_custom_dev.py."""
import os
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.model.base_document import get_controller
from frappe.model.document import Document
from powerpro.custom_hr import installer


@unittest.skipUnless(os.environ.get("POWERPRO_HR_CUSTOM_DEV") == "1", "Explicit isolated Development runner required")
class CustomHRMigrationTest(unittest.TestCase):
    def setUp(self):
        frappe.db.savepoint("custom_hr_test")
        self.addCleanup(self.cleanup)

    def cleanup(self):
        frappe.db.rollback(save_point="custom_hr_test")
        installer._refresh()

    def test_final_controller_resolution(self):
        overrides = frappe.get_hooks("override_doctype_class")
        retained = []
        for name in installer.NAMES:
            self.assertEqual(frappe.db.get_value("DocType", name, "custom"), 1)
            controller = get_controller(name)
            if name in overrides:
                self.assertEqual(controller, frappe.get_attr(overrides[name][-1]))
                self.assertTrue(controller.__module__.startswith("powerpro.controllers.hr_custom."))
                retained.append(name)
            else:
                self.assertIs(controller, Document)
        self.assertEqual(len(retained), 11)
        self.assertIn("check_if_latest", get_controller("Ordinary Night Automation").__dict__)
        self.assertTrue(callable(getattr(get_controller("Ordinary Night Automation"), "validate_policy")))
        self.assertIn("check_if_latest", get_controller("Ordinary Night Settlement").__dict__)

    def test_repeat_install_does_not_save_scripts(self):
        before = {(doc["doctype"], doc["name"]): frappe.db.get_value(doc["doctype"], doc["name"], "modified")
                  for doc in installer.scripts()}
        installer.install()
        after = {(dt, name): frappe.db.get_value(dt, name, "modified") for dt, name in before}
        self.assertEqual(before, after)
        self.assertEqual(installer.preview()["conflicts"], [])

    def test_entry_point_repairs_stale_generic_controller(self):
        name = "Ordinary Night Automation"
        expected = get_controller(name)
        frappe.controllers[frappe.local.site][name] = Document
        installer.initialize_controllers(method="test", kwargs={})
        self.assertIs(get_controller(name), expected)

    def test_metadata_drift_refused_before_any_conversion(self):
        field = frappe.db.get_value("DocField", {"parent": "Working Time Review", "fieldname": "employee"}, "name")
        frappe.db.set_value("DocField", field, "fieldtype", "Data", update_modified=False)
        frappe.clear_cache(doctype="Working Time Review")
        with self.assertRaises(frappe.ValidationError):
            installer.install()

    def test_modified_owned_script_is_not_overwritten(self):
        doc = installer.scripts()[0]
        frappe.db.set_value(doc["doctype"], doc["name"], "script", "// locally edited", update_modified=False)
        installer.install()
        self.assertEqual(frappe.db.get_value(doc["doctype"], doc["name"], "script"), "// locally edited")

    def test_missing_required_script_is_repaired(self):
        doc = installer.scripts()[0]
        # Simulate an interrupted metadata install, without deletion's cleanup job.
        frappe.db.delete(doc["doctype"], {"name": doc["name"]})
        installer.install()
        self.assertEqual(frappe.db.get_value(doc["doctype"], doc["name"], "script"), doc["script"])

    def test_server_script_configuration_is_required(self):
        with patch("frappe.utils.safe_exec.is_safe_exec_enabled", return_value=False):
            with self.assertRaises(frappe.ValidationError):
                installer.install()

    def test_outbound_binding_requires_event_order_review(self):
        frappe.get_doc(dict(doctype="Notification", name="HR-CUSTOM-NOTIFICATION-PROBE",
                            document_type="Overtime Reconciliation Run", enabled=1, event="Save")).db_insert()
        with self.assertRaisesRegex(frappe.ValidationError, "event-order review"):
            installer.install()

    def test_before_image_creation_is_retry_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            target = str(Path(directory) / "before.json")
            Path(directory, "before.tmp").write_text("interrupted older attempt")
            with patch.object(frappe, "get_site_path", return_value=target):
                installer._snapshot()
                original = Path(target).read_bytes()
                installer._snapshot()
                self.assertEqual(Path(target).read_bytes(), original)
                self.assertEqual(Path(target).stat().st_mode & 0o777, 0o600)

    def test_all_guards_run_in_full_document_event_pipeline(self):
        method = {"Before Save": "validate", "Before Delete": "on_trash", "Before Rename": "before_rename"}
        for script in installer.scripts():
            if script["doctype"] != "Server Script" or script["reference_doctype"] not in {"Overtime Reconciliation Run", "Overtime Attendance Exception", "Lote de Pago de Dietas"}:
                continue
            with self.subTest(script=script["name"]):
                doc = frappe.get_doc(dict(doctype=script["reference_doctype"], name="HR-CUSTOM-GUARD-PROBE"))
                error = frappe.ValidationError if doc.doctype == "Overtime Reconciliation Run" else frappe.PermissionError
                with self.assertRaises(error):
                    doc.run_method(method[script["doctype_event"]])
                self.assertFalse(frappe.db.exists(doc.doctype, doc.name))
        batch = frappe.get_doc(dict(doctype="Lote de Pago de Dietas", name="HR-CUSTOM-GUARD-PROBE"))
        batch.flags.dieta_service = True
        batch.run_method("validate")

    def test_inverse_refuses_unsafe_rollback(self):
        before = json.loads(Path(frappe.get_site_path("private", "backups", installer.SNAPSHOT)).read_text())
        if any(value is None for value in before["doctypes"].values()):
            with self.assertRaisesRegex(frappe.ValidationError, "Fresh-install rollback requires"):
                installer.rollback()
            return
        frappe.db.set_value("DocType", "Working Time Review", "description", "changed after migration", update_modified=False)
        with self.assertRaisesRegex(frappe.ValidationError, "HR metadata changed after conversion"):
            installer.rollback()

    def test_release_update_and_owner_conflict(self):
        original = installer.scripts()
        changed = [dict(doc) for doc in original]
        changed[0]["script"] += "\n// upstream change\n"
        with patch.object(installer, "scripts", return_value=changed):
            installer.install()
        doc = changed[0]
        self.assertEqual(frappe.db.get_value(doc["doctype"], doc["name"], "script"), doc["script"])
        frappe.db.set_value(doc["doctype"], doc["name"], "script", doc["script"] + "// owner change")
        changed[0] = dict(doc, script=doc["script"] + "// another upstream change")
        with patch.object(installer, "scripts", return_value=changed):
            with self.assertRaisesRegex(frappe.ValidationError, "both owner and release"):
                installer.install()

    def test_owner_enablement_and_identity(self):
        name = installer.PREFIX + "Working Time Review - Before Save"
        frappe.db.set_value("Server Script", name, "disabled", 1)
        installer.install()
        self.assertEqual(frappe.db.get_value("Server Script", name, "disabled"), 1)
        frappe.db.set_value("Server Script", name, "doctype_event", "Before Delete")
        with self.assertRaisesRegex(frappe.ValidationError, "identity conflict"):
            installer.install()

    def test_no_business_event_methods_or_rpc_capabilities_remain(self):
        methods = {"validate", "before_validate", "before_submit", "on_submit", "before_cancel",
                   "on_cancel", "on_update", "on_update_after_submit", "before_update_after_submit",
                   "on_trash", "before_rename"}
        for name in installer.NAMES:
            cls = get_controller(name)
            self.assertFalse(methods.intersection(cls.__dict__), name)
            if cls is Document:
                continue
            for base in cls.__mro__:
                if not base.__module__.startswith("powerpro.controllers.hr_custom"):
                    continue
                for method in base.__dict__.values():
                    if callable(method):
                        self.assertNotIn(method, frappe.whitelisted)

    def test_trusted_flags_and_revision_identity_in_event_pipeline(self):
        for dt, flag in [("Working Time Review", "working_time_incident_write"),
                         ("Working Time Incident", "working_time_incident_write"),
                         ("Overtime Rest Watch", "overtime_rest_watch_write"),
                         ("Overtime Evidence Watch", "overtime_evidence_monitor_write")]:
            doc = frappe.get_doc(dict(doctype=dt, name="HR-CUSTOM-GUARD"))
            with patch.dict(frappe.flags, {flag: False}):
                with self.assertRaises(frappe.PermissionError):doc.run_method("validate")
            with patch.dict(frappe.flags, {flag: True}):doc.run_method("validate")
            with self.assertRaises(frappe.PermissionError):doc.run_method("on_trash")
        from powerpro.supplements.service import trusted
        doc = frappe.new_doc("Employee Supplement Revision")
        with self.assertRaises(frappe.ValidationError):doc.run_method("validate")
        trusted(doc).run_method("validate")
        with self.assertRaises(frappe.ValidationError):doc.run_method("on_trash")

    def test_policy_rules_execute_in_sandbox(self):
        doc = frappe.get_doc(dict(doctype="Overtime Pay Policy", company="TEST", valid_from="2026-01-01",
            valid_until="2026-12-31", approval_reference="test", regular_percent=35, extraordinary_percent=100,
            night_percent=15, weekly_rest_percent=100, weekly_threshold=44, night_basis="Clock overlap",
            premium_combination="Additive on base hour", approved_by="forged", approved_on="2026-01-01"))
        doc.run_method("validate")
        self.assertIsNone(doc.approved_by)
        for bad in [14, float("inf"), float("nan")]:
            doc.night_percent = bad
            with self.assertRaises(frappe.ValidationError):doc.run_method("validate")
        for dt in ["Overtime Pay Policy", "Ordinary Night Settlement", "Overtime Settlement Election"]:
            with self.assertRaises(frappe.ValidationError):
                frappe.new_doc(dt).run_method("before_update_after_submit")

    def test_owner_policy_edit_reaches_form_and_worker_and_survives_install(self):
        name = installer.PREFIX + "Ordinary Night Automation - Before Save"
        script = frappe.get_doc("Server Script", name)
        script.script = "def validate_policy(doc):\n    frappe.throw('owner policy rule')\n\nvalidate_policy(doc)\n"
        script.save(ignore_permissions=True)
        installer.install()
        doc = frappe.new_doc("Ordinary Night Automation")
        for call in [lambda: doc.run_method("validate"), doc.validate_policy]:
            with self.assertRaisesRegex(frappe.ValidationError, "owner policy rule"):call()
        script.reload()
        script.disabled = 1
        script.save(ignore_permissions=True)
        with self.assertRaisesRegex(frappe.ValidationError, "unavailable"):doc.validate_policy()

    def test_worker_rule_stays_sandboxed_and_requires_export(self):
        name = installer.PREFIX + "Ordinary Night Automation - Before Save"
        doc = frappe.new_doc("Ordinary Night Automation")
        frappe.db.set_value("Server Script", name, "script", "def validate_policy(doc):\n    import os\n")
        with self.assertRaises(ImportError):doc.validate_policy()
        frappe.db.set_value("Server Script", name, "script", "doc.reference = 'no export'")
        with self.assertRaisesRegex(frappe.ValidationError, "must export"):doc.validate_policy()

    def test_inverse_reapply_restores_required_scripts(self):
        before = json.loads(Path(frappe.get_site_path("private", "backups", installer.SNAPSHOT)).read_text())
        if any(value is None for value in before["doctypes"].values()):
            return  # Fresh schema creation has a separate isolated recovery boundary.
        installer.rollback()
        for key, original in before["scripts"].items():
            dt, name = key.split(":", 1)
            if original is None:
                self.assertFalse(frappe.db.exists(dt, name))
            else:
                self.assertEqual(frappe.db.get_value(dt, name, "script"), original["script"])
        installer.install()
        for doc in installer.scripts():
            if doc["doctype"] == "Server Script":
                self.assertEqual(frappe.db.get_value("Server Script", doc["name"], "disabled"), 0)

    def test_inverse_refuses_owner_edits_since_upgrade(self):
        name = installer.PREFIX + "Working Time Review - Before Save"
        with tempfile.TemporaryDirectory() as directory:
            target = str(Path(directory) / "before.json")
            with patch.object(frappe, "get_site_path", return_value=target):
                installer._snapshot()
                frappe.db.set_value("Server Script", name, "script", "# owner edit since upgrade")
                with self.assertRaisesRegex(frappe.ValidationError, "script changed"):
                    installer.rollback()
