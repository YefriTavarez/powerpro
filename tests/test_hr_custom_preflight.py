"""Installer preflight regressions runnable without Frappe or a database."""
import copy
import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]


class Record(dict):
    def __getattr__(self, key):
        return self.get(key)

    def as_dict(self):
        return self


class PreflightTest(unittest.TestCase):
    def setUp(self):
        self.frappe = types.ModuleType("frappe")
        self.frappe.db = Mock()
        self.frappe.local = types.SimpleNamespace(site="isolated.test")
        self.frappe.get_hooks = Mock()
        self.frappe.get_site_path = Mock()
        self.frappe.throw = Mock(side_effect=ValueError)
        spec = importlib.util.spec_from_file_location(
            "isolated_hr_installer", ROOT / "powerpro/custom_hr/installer.py")
        self.installer = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"frappe": self.frappe}):
            spec.loader.exec_module(self.installer)
        self.records = {
            ("DocType", name): Record(value, custom=1)
            for name, value in self.installer.definitions().items()
        }
        self.records.update({(value["doctype"], value["name"]): Record(value)
                             for value in self.installer.scripts()})
        self.baseline = {self.installer._script_key(doc): self.installer._upstream_record(doc)
                         for doc in self.installer.scripts()}
        self.frappe.db.exists.side_effect = lambda dt, name: (dt, name) in self.records
        self.frappe.get_doc = Mock(side_effect=lambda dt, name: self.records[(dt, name)])
        self.frappe.db.get_value.side_effect = self.get_value
        self.frappe.get_all = Mock(side_effect=self.get_all)

    def get_value(self, dt, name, field):
        if dt == "DefaultValue":
            return json.dumps(self.baseline) if self.baseline is not None else None
        return self.records.get((dt, name), {}).get(field)

    def get_all(self, dt, filters, pluck):
        return [name for (doctype, name), doc in self.records.items()
                if doctype == dt and all(doc.get(k) == v for k, v in filters.items())]

    def field(self, dt, name):
        return next(row for row in self.records[("DocType", dt)]["fields"] if row["fieldname"] == name)

    def extend_dietas(self):
        self.records[("DocType", "Solicitud de Dieta")]["fields"].insert(
            0, dict(fieldname="work_order", fieldtype="Link", options="Work Order"))
        self.field("Solicitud de Dieta", "company")["reqd"] = 0
        batch = self.records[("DocType", "Lote de Pago de Dietas")]
        batch["fields"].append(dict(fieldname="standalone_details", fieldtype="Long Text"))
        self.field(batch["name"], "overtime_work_call")["reqd"] = 0
        self.field(batch["name"], "status")["options"] = "Draft\nConfirmed\nReversed"
        self.extra_list = "Site dieta list"
        self.records[("Client Script", self.extra_list)] = Record(
            doctype="Client Script", name=self.extra_list, dt=batch["name"],
            view="List", enabled=1, script="// independent list customization")

    def test_installed_dietas_extensions_and_owned_edits_are_preserved(self):
        self.extend_dietas()
        name = self.installer.PREFIX + "Lote de Pago de Dietas"
        self.records[("Client Script", name)]["script"] = "// owner customization"
        before = copy.deepcopy(self.records)
        report = self.installer.preview()
        self.assertEqual(report["conflicts"], [])
        self.assertEqual(report["preserved_customizations"], [
            "Lote de Pago de Dietas: existing Client Script " + self.extra_list])
        desired, conflicts = self.installer._script_plan()
        self.assertEqual(conflicts, [])
        self.assertEqual(next(doc for doc in desired if doc["name"] == name)["script"],
                         "// owner customization")
        self.assertNotIn(self.extra_list, [doc["name"] for doc in desired])
        self.assertEqual(self.records, before)
        for operation in ("set_value", "delete", "set_global", "commit"):
            getattr(self.frappe.db, operation).assert_not_called()
        self.frappe.get_hooks.assert_not_called()
        self.frappe.get_site_path.assert_not_called()

    def test_custom_flag_without_successful_baseline_is_not_an_upgrade(self):
        self.extend_dietas()
        for baseline in (None, {}):
            with self.subTest(baseline=baseline):
                self.baseline = baseline
                conflicts = self.installer.preview()["conflicts"]
                self.assertTrue(any("fields row count" in item for item in conflicts))
                self.assertTrue(any("field_order" in item for item in conflicts))
                self.assertTrue(any(self.extra_list in item for item in conflicts))

    def test_standard_doctype_conversion_stays_strict_even_with_baseline(self):
        self.extend_dietas()
        self.records[("DocType", "Lote de Pago de Dietas")]["custom"] = 0
        report = self.installer.preview()
        self.assertTrue(any("Lote de Pago de Dietas: definition differs at fields row count" == item
                            for item in report["conflicts"]))
        self.assertTrue(any(self.extra_list in item for item in report["conflicts"]))

    def test_reordered_fields_are_preserved_on_repeated_previews(self):
        self.extend_dietas()
        self.records[("DocType", "Solicitud de Dieta")]["fields"].reverse()
        before = copy.deepcopy(self.records)
        self.assertEqual(self.installer.preview()["conflicts"], [])
        self.assertEqual(self.installer.preview()["conflicts"], [])
        self.assertEqual(before, self.records)

    def test_missing_release_field_fails_even_when_counts_match(self):
        self.extend_dietas()
        fields = self.records[("DocType", "Lote de Pago de Dietas")]["fields"]
        fields[:] = [row for row in fields if row["fieldname"] != "company"]
        self.assertIn("Lote de Pago de Dietas: definition differs at fields.company: missing release field",
                      self.installer.preview()["conflicts"])

    def test_incompatible_type_and_link_target_are_detected_among_extra_fields(self):
        self.extend_dietas()
        self.field("Solicitud de Dieta", "company")["fieldtype"] = "Data"
        self.field("Lote de Pago de Dietas", "rows")["options"] = "Wrong Child"
        conflicts = self.installer.preview()["conflicts"]
        self.assertIn("Solicitud de Dieta: definition differs at fields.company.fieldtype", conflicts)
        self.assertIn("Lote de Pago de Dietas: definition differs at fields.rows.options", conflicts)

    def test_removed_select_choice_is_not_an_extension(self):
        self.extend_dietas()
        self.field("Lote de Pago de Dietas", "status")["options"] = "Draft\nConfirmed"
        self.assertIn("Lote de Pago de Dietas: definition differs at fields.status.options",
                      self.installer.preview()["conflicts"])

    def test_select_choice_reordering_is_compatible(self):
        self.field("Lote de Pago de Dietas", "status")["options"] = "Reversed\nDraft\nConfirmed"
        self.assertEqual(self.installer.preview()["conflicts"], [])

    def test_duplicate_field_names_fail(self):
        fields = self.records[("DocType", "Solicitud de Dieta")]["fields"]
        fields.append(dict(self.field("Solicitud de Dieta", "company")))
        self.assertTrue(any("duplicate fieldname 'company'" in item
                            for item in self.installer.preview()["conflicts"]))

    def test_schema_identity_permissions_and_field_guards_stay_strict(self):
        for change in ("istable", "permissions", "read_only"):
            with self.subTest(change=change):
                before = copy.deepcopy(self.records)
                doc = self.records[("DocType", "Lote de Pago de Dietas")]
                if change == "istable":
                    doc[change] = 1
                elif change == "permissions":
                    doc[change][0]["read"] = 0
                else:
                    self.field(doc["name"], "status")[change] = 0
                self.assertTrue(self.installer.preview()["conflicts"])
                self.records = before

    def test_form_scripts_and_other_bindings_still_require_review(self):
        self.extend_dietas()
        self.records[("Client Script", self.extra_list)]["view"] = "Form"
        for dt, field in (("Custom Field", "dt"), ("Property Setter", "doc_type"),
                          ("Workflow", "document_type"), ("Server Script", "reference_doctype")):
            self.records[(dt, "site override")] = Record({field: "Lote de Pago de Dietas"})
        conflicts = self.installer.preview()["conflicts"]
        for dt in ("Client Script", "Custom Field", "Property Setter", "Workflow", "Server Script"):
            self.assertTrue(any("existing " + dt in item for item in conflicts), dt)

    def test_outbound_bindings_still_require_event_order_review(self):
        for dt, field in (("Notification", "document_type"), ("Webhook", "webhook_doctype")):
            self.records[(dt, "outbound")] = Record({field: "Solicitud de Dieta", "enabled": 1})
        conflicts = self.installer.preview()["conflicts"]
        self.assertEqual(sum("event-order review" in item for item in conflicts), 2)

    def test_simultaneous_owner_and_release_script_change_fails(self):
        self.extend_dietas()
        original = self.installer.scripts()
        changed = copy.deepcopy(original)
        changed[0]["script"] += "\n// release edit"
        self.records[(original[0]["doctype"], original[0]["name"])]["script"] += "\n// owner edit"
        with patch.object(self.installer, "scripts", return_value=changed):
            self.assertTrue(any("both owner and release" in item
                                for item in self.installer.preview()["conflicts"]))

    def test_script_rebinding_and_disabled_flags_remain_protected(self):
        doc = next(doc for doc in self.installer.scripts() if doc["doctype"] == "Server Script")
        current = self.records[(doc["doctype"], doc["name"])]
        current["disabled"] = 1
        desired, conflicts = self.installer._script_plan()
        self.assertEqual(conflicts, [])
        self.assertEqual(next(row for row in desired if row["name"] == doc["name"])["disabled"], 1)
        current["doctype_event"] = "After Save"
        self.assertTrue(any("identity conflict" in item for item in self.installer.preview()["conflicts"]))

    def test_conflict_aborts_install_before_snapshot_or_writes(self):
        self.extend_dietas()
        self.field("Solicitud de Dieta", "company")["fieldtype"] = "Data"
        safe_exec = types.ModuleType("frappe.utils.safe_exec")
        safe_exec.is_safe_exec_enabled = lambda: True
        with patch.dict(sys.modules, {"frappe.utils.safe_exec": safe_exec}), \
                patch.object(self.installer, "_snapshot") as snapshot, \
                patch.object(self.installer, "_refresh") as refresh:
            with self.assertRaises(ValueError):
                self.installer.install()
            snapshot.assert_not_called()
            refresh.assert_not_called()
        self.frappe.db.set_value.assert_not_called()


if __name__ == "__main__":
    unittest.main()
