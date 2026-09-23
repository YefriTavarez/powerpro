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
        with self.assertRaises(frappe.ValidationError):
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
            if script["doctype"] != "Server Script":
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
