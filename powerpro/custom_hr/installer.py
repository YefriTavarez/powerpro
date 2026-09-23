"""Install the narrowly scoped HR metadata without rewriting existing definitions.

Called before model sync on upgrades and after standard model sync on new app
installations. Not whitelisted. Callers own maintenance windows and transactions.
"""
import hashlib
import json
import os
import tempfile
from pathlib import Path

import frappe

ROOT = Path(__file__).parent
MANIFEST = json.loads((ROOT / "manifest.json").read_text())
NAMES = tuple(row["name"] for row in MANIFEST["doctypes"])
PREFIX = "PowerPro HR v1 - "
SNAPSHOT = "powerpro-hr-custom-v1-before.json"
IGNORE = {"creation", "modified", "modified_by", "owner", "doctype", "custom", "__islocal"}


def definitions():
    result = {
        row["name"]: json.loads((ROOT / "definitions" / (row["slug"] + ".json")).read_text())
        for row in MANIFEST["doctypes"]
    }
    # Standard JSON may store fields in a different order than field_order.
    # Match DocType.prepare_for_import before comparing or inserting metadata.
    for doc in result.values():
        if doc.get("field_order"):
            fields = {field["fieldname"]: field for field in doc["fields"]}
            if set(fields) != set(doc["field_order"]):
                raise ValueError("Incomplete field_order: " + doc["name"])
            doc["fields"] = [fields[name] for name in doc["field_order"]]
    return result


def ordered_definitions():
    remaining = definitions()
    while remaining:
        ready = [name for name, doc in remaining.items() if not any(
            field.get("options") in remaining and field.get("options") != name
            for field in doc["fields"] if field["fieldtype"] in ("Link", "Table", "Table MultiSelect")
        )]
        if not ready:
            raise ValueError("Circular HR definition dependencies: " + ", ".join(remaining))
        for name in ready:
            yield remaining.pop(name)


def scripts(include_server_scripts=True):
    result = []
    for row in MANIFEST["doctypes"]:
        if row.get("client_script"):
            result.append(dict(doctype="Client Script", name=PREFIX + row["name"],
                dt=row["name"], view="Form", enabled=1,
                script=(ROOT / "client_scripts" / (row["slug"] + ".js")).read_text()))
    for row in MANIFEST["server_scripts"]:
        result.append(dict(doctype="Server Script", name=PREFIX + row["doctype"] + " - " + row["event"],
            script_type="DocType Event", reference_doctype=row["doctype"], doctype_event=row["event"],
            disabled=int(not include_server_scripts),
            script=(ROOT / "server_scripts" / row["file"]).read_text()))
    return result


def _equal(actual, expected):
    if actual in (None, "") and expected in (None, ""):
        return True
    if isinstance(expected, (int, float)):
        return (actual or 0) == expected
    return actual == expected


def _definition_conflicts(actual, expected):
    conflicts = []
    for key, value in expected.items():
        if key in IGNORE or key == "field_order":
            continue
        if isinstance(value, list):
            rows = actual.get(key) or []
            if len(rows) != len(value):
                conflicts.append(key + " row count")
                continue
            for index, (saved, source) in enumerate(zip(rows, value)):
                for field, expected_value in source.items():
                    if field not in IGNORE and not _equal(saved.get(field), expected_value):
                        conflicts.append(f"{key}[{index}].{field}")
        elif not _equal(actual.get(key), value):
            conflicts.append(key)
    # field_order is encoded by DocField.idx in the database.
    order = expected.get("field_order")
    if order and [row.get("fieldname") for row in actual.get("fields", [])] != order:
        conflicts.append("field_order")
    return conflicts


def _fingerprint(doc):
    value = dict(doc)
    value.pop("custom", None)
    return hashlib.sha256(frappe.as_json(value).encode()).hexdigest()


def preview(include_server_scripts=True):
    """Read-only preflight; no cache invalidation or record creation."""
    report = {"version": 1, "site": frappe.local.site, "doctypes": [], "conflicts": []}
    owned = {(doc["doctype"], doc["name"]) for doc in scripts(include_server_scripts)}
    for name, expected in definitions().items():
        exists = frappe.db.exists("DocType", name)
        custom = None
        if exists:
            actual = frappe.get_doc("DocType", name).as_dict()
            custom = actual.custom
            for conflict in _definition_conflicts(actual, expected):
                report["conflicts"].append(f"{name}: definition differs at {conflict}")
        report["doctypes"].append({"name": name, "action": "create" if not exists else "keep" if custom else "convert"})
        # Never silently absorb site-level behavior or metadata customizations.
        for dt, field in (("Custom Field", "dt"), ("Property Setter", "doc_type"),
                          ("Workflow", "document_type"), ("Client Script", "dt"),
                          ("Server Script", "reference_doctype")):
            for row in frappe.get_all(dt, filters={field: name}, pluck="name"):
                if (dt, row) not in owned:
                    report["conflicts"].append(f"{name}: existing {dt} {row}")
    for expected in scripts(include_server_scripts):
        if frappe.db.exists(expected["doctype"], expected["name"]):
            current = frappe.get_doc(expected["doctype"], expected["name"])
            for key, value in expected.items():
                if key not in ("enabled", "disabled") and not _equal(current.get(key), value):
                    report["conflicts"].append(f"{expected['name']}: script conflict at {key}")
    if include_server_scripts:
        # These run before Server Scripts in Document.run_method. New outbound
        # bindings need review before replacing an early Python rejection.
        for name in {row["doctype"] for row in MANIFEST["server_scripts"]}:
            for dt, field in (("Notification", "document_type"), ("Webhook", "webhook_doctype")):
                for binding in frappe.get_all(dt, filters={field: name, "enabled": 1}, pluck="name"):
                    report["conflicts"].append(f"{name}: enabled {dt} requires event-order review: {binding}")
    return report


def _require_clean(report):
    if report["conflicts"]:
        frappe.throw("HR Custom DocType preflight failed:\n" + "\n".join(report["conflicts"]))


def _snapshot():
    path = Path(frappe.get_site_path("private", "backups", SNAPSHOT))
    if path.exists():
        data = json.loads(path.read_text())
        if data.get("site") != frappe.local.site or set(data.get("doctypes", {})) != set(NAMES):
            frappe.throw("Invalid HR migration before-image; inspect the private snapshot.")
        return data
    data = {"version": 1, "site": frappe.local.site, "doctypes": {}, "scripts": {}}
    for name in NAMES:
        data["doctypes"][name] = frappe.get_doc("DocType", name).as_dict() if frappe.db.exists("DocType", name) else None
    for doc in scripts():
        key = doc["doctype"] + ":" + doc["name"]
        data["scripts"][key] = frappe.get_doc(doc["doctype"], doc["name"]).as_dict() if frappe.db.exists(doc["doctype"], doc["name"]) else None
    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic creation; never overwrite the original before-image on a retry.
    # A unique temporary name allows a retry after an interrupted preflight.
    fd, temporary = tempfile.mkstemp(prefix=SNAPSHOT + ".", dir=path.parent)
    temp = Path(temporary)
    try:
        with os.fdopen(fd, "w") as output:
            output.write(frappe.as_json(data)); output.flush(); os.fsync(output.fileno())
        os.link(temp, path)
    finally:
        temp.unlink(missing_ok=True)
    return data


def _refresh():
    # Clear process-local classes too; Redis metadata invalidation is insufficient.
    frappe.get_hooks()
    for name in NAMES:
        frappe.clear_cache(doctype=name)
        frappe.controllers.setdefault(frappe.local.site, {}).pop(name, None)
    frappe.cache.delete_value("server_script_map")


def initialize_controllers(**kwargs):
    """Import PowerPro's existing loader even when hooks came from Redis.

    Web and job entry points call this before business documents are resolved.
    Keep correct cached classes; discard only stale classes within this scope.
    Importing this module already imports powerpro and installs its loader.
    """
    cached = frappe.controllers.get(frappe.local.site, {})
    overrides = frappe.get_hooks("override_doctype_class")
    for name in NAMES:
        controller = cached.get(name)
        if controller is None:
            continue
        expected = (overrides.get(name) or ["frappe.model.document.Document"])[-1]
        if controller.__module__ + "." + controller.__name__ != expected:
            cached.pop(name, None)


def install(include_server_scripts=True):
    """Convert in place, create missing definitions, and install owned scripts.

    Existing DocTypes only change the custom flag. No schema update, business
    document save, explicit commit, payroll action, or global fixture overwrite.
    Creating absent DocTypes necessarily performs DDL; caller must checkpoint.
    """
    from frappe.utils.safe_exec import is_safe_exec_enabled

    if include_server_scripts and not is_safe_exec_enabled():
        frappe.throw("Enable Server Scripts before installing HR Custom DocTypes.")
    frappe.get_hooks()  # Load the existing PowerPro custom-controller loader first.
    report = preview(include_server_scripts)
    _require_clean(report)
    _snapshot()
    for definition in ordered_definitions():
        name = definition["name"]
        if frappe.db.exists("DocType", name):
            if not frappe.db.get_value("DocType", name, "custom"):
                frappe.db.set_value("DocType", name, "custom", 1, update_modified=False)
        else:
            definition["custom"] = 1
            # Match standard JSON import semantics. Normal DocType.insert()
            # adds amended_from to submittable types even when the versioned
            # standard definition deliberately has no such field.
            from frappe.core.doctype.doctype.doctype import make_module_and_roles
            from frappe.modules.import_file import import_doc
            make_module_and_roles(frappe.get_doc(definition))
            importing = frappe.flags.in_import
            try:
                # This path is strictly for absent metadata. import_doc must
                # never delete/recreate an existing DocType during conversion.
                import_doc(definition, ignore_version=True)
            finally:
                frappe.flags.in_import = importing
    _refresh()
    for expected in scripts(include_server_scripts):
        if not frappe.db.exists(expected["doctype"], expected["name"]):
            frappe.get_doc(expected).insert(ignore_permissions=True)
        else:
            doc = frappe.get_doc(expected["doctype"], expected["name"])
            changed = {key: value for key, value in expected.items() if not _equal(doc.get(key), value)}
            if changed:
                doc.update(changed)
                doc.save(ignore_permissions=True)
    _refresh()
    return report


def rollback():
    """Inverse for an existing-site conversion, after restoring matching code.

    Refuse fresh-install deletion and intervening definition/script changes.
    Caller must pause writers and reconcile any post-cutover business activity.
    """
    path = Path(frappe.get_site_path("private", "backups", SNAPSHOT))
    if not path.is_file():
        frappe.throw("HR migration before-image is missing.")
    before = json.loads(path.read_text())
    if before.get("site") != frappe.local.site or set(before.get("doctypes", {})) != set(NAMES):
        frappe.throw("HR migration before-image does not match this site and scope.")
    for name, doc in before["doctypes"].items():
        if doc is None:
            frappe.throw("Fresh-install rollback requires isolated checkpoint recovery; no DocTypes will be deleted.")
        if _fingerprint(frappe.get_doc("DocType", name).as_dict()) != _fingerprint(doc):
            frappe.throw("HR metadata changed after conversion: " + name)
    # Validate every owned script before making any inverse changes.
    for expected in scripts():
        if frappe.db.exists(expected["doctype"], expected["name"]):
            current = frappe.get_doc(expected["doctype"], expected["name"])
            if any(not _equal(current.get(key), value) for key, value in expected.items() if key not in ("enabled", "disabled")):
                frappe.throw("HR script changed after conversion: " + expected["name"])
    for name, doc in before["doctypes"].items():
        frappe.db.set_value("DocType", name, "custom", doc.get("custom", 0), update_modified=False)
    for expected in scripts():
        dt, name = expected["doctype"], expected["name"]
        original = before["scripts"][dt + ":" + name]
        if frappe.db.exists(dt, name):
            key = "enabled" if dt == "Client Script" else "disabled"
            value = original.get(key) if original else int(key == "disabled")
            frappe.db.set_value(dt, name, key, value, update_modified=False)
    _refresh()
    return {"restored_custom_flags": len(NAMES), "site": frappe.local.site}
