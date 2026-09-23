"""Non-RPC capabilities unavailable through the Server Script namespace.

Business rules belong to the document-event scripts. These methods expose no
imports, arbitrary call targets, transaction control or HTTP endpoints.
"""
import ast
import hashlib

import frappe
from frappe.model.document import Document
from powerpro.controllers.overtime import _reconciliation_rows


class HRScriptDocument(Document):
    def claim_digest(self, value):
        """Stable unique claim keys require hashlib, unavailable in safe_exec."""
        return hashlib.sha256(value.encode()).hexdigest()

    def current_roles(self):
        """safe_exec does not expose get_roles."""
        return frappe.get_roles()

    def locked_rows(self, doctype, *, filters, fields=None, pluck=None, limit=1000):
        """Current reads, rather than old MVCC snapshots, under held locks."""
        if not isinstance(limit, int) or not 1 <= limit <= 1001:
            raise ValueError("HR locking queries require a limit from 1 to 1001")
        if doctype not in {
            self.doctype, "Overtime Pay Policy", "Overtime Authorization",
            "Retroactive Overtime Adjustment",
        }:
            raise ValueError("Unsupported HR locking query")
        return _reconciliation_rows(doctype, for_update=True, filters=filters,
                                    fields=fields, pluck=pluck, limit=limit)


def automation_policy_for_worker(doc):
    """Run the same exported rule used by the form, without form mutations.

    Frappe has no document-method Server Script event. Only function definitions
    are selected from this fixed, enabled script; execution still uses safe_exec
    and the document-event commit/rollback restrictions. No Python exec/eval.
    """
    from frappe.utils.safe_exec import safe_exec

    name = "PowerPro HR v1 - Ordinary Night Automation - Before Save"
    script = frappe.get_doc("Server Script", name)
    if (script.disabled or script.script_type != "DocType Event"
            or script.reference_doctype != "Ordinary Night Automation"
            or script.doctype_event != "Before Save"):
        frappe.throw("The Ordinary Night Automation policy script is unavailable.")
    definitions = [node for node in ast.parse(script.script).body if isinstance(node, ast.FunctionDef)]
    if not any(node.name == "validate_policy" for node in definitions):
        frappe.throw("The automation script must export validate_policy(doc).")
    module = ast.Module(body=definitions + ast.parse("validate_policy(doc)").body, type_ignores=[])
    safe_exec(ast.unparse(module), _globals={"doc": doc},
              restrict_commit_rollback=True, script_filename=name)
