import base64
import re

import frappe
import requests


DB_TEMPLATE_CALL_RE = re.compile(
	r"""frappe\.(?:db\.)?get_value\(
		\s*(['"])(?P<doctype>.*?)\1\s*,
		\s*(?P<name_expr>[^,]+?)\s*,
		\s*(['"])(?P<fieldname>.*?)\4\s*
	\)""",
	re.VERBOSE,
)


class PrintCardPdfClient:
	"""Client for the DB-free PrintCard PDF endpoint."""

	def __init__(self, method_path=None):
		settings = frappe.get_single("Power-Pro Settings")
		self.base_url = (settings.get("printcard_client_base_url") or "").rstrip("/")
		self.username = settings.get("printcard_client_username")
		self.password = settings.get_password("printcard_client_password")
		self.timeout = settings.get("printcard_client_timeout_seconds") or 30
		self.method_path = method_path or "/api/method/powerpro.controllers.printcard.helper.generate_pdf_from_payload"

		if not self.base_url:
			frappe.throw("Missing 'printcard_client_base_url' in Power-Pro Settings.")
		if not self.username:
			frappe.throw("Missing 'printcard_client_username' in Power-Pro Settings.")
		if not self.password:
			frappe.throw("Missing 'printcard_client_password' in Power-Pro Settings.")

	def generate_pdf(self, payload):
		response_data = self.generate_pdf_response(payload)
		pdf_b64 = response_data.get("pdf_base64")
		if not pdf_b64:
			frappe.throw("The PrintCard PDF endpoint returned no 'pdf_base64' value.")
		return base64.b64decode(pdf_b64)

	def generate_pdf_response(self, payload):
		if not isinstance(payload, dict):
			frappe.throw("Payload must be a dict.")

		request_payload = self._prepare_payload(payload)
		url = f"{self.base_url}{self.method_path}"
		resp = requests.post(
			url,
			json=request_payload,
			auth=(self.username, self.password),
			timeout=self.timeout,
		)

		if resp.status_code >= 400:
			frappe.throw(f"PrintCard PDF API returned HTTP {resp.status_code}: {resp.text}")

		try:
			data = resp.json()
		except ValueError as err:
			frappe.throw(f"Invalid JSON response from PrintCard PDF API: {err}")

		if not data.get("ok"):
			error = data.get("error") or {}
			frappe.throw(error.get("message") or "PrintCard PDF API returned an error.")

		return data

	def _prepare_payload(self, payload):
		canvas = dict(payload.get("canvas") or {})
		doc = payload.get("doc") or {}
		lookups = payload.get("lookups") or {}
		safety = dict(payload.get("safety") or {})
		options = dict(payload.get("options") or {})

		html_template = canvas.get("codigo_html") or ""
		resolved_html, diagnostics = resolve_db_template_calls(
			html_template=html_template,
			doc=doc,
			lookups=lookups,
		)
		canvas["codigo_html"] = resolved_html

		if diagnostics["remaining_calls"] > 0:
			frappe.throw(
				f"Template still has unresolved DB calls: {diagnostics['remaining_calls']}. "
				f"Examples: {diagnostics['unresolved'][:3]}"
			)

		safety.setdefault("allow_frappe_proxy", False)

		return {
			"pdf_base64": payload.get("pdf_base64"),
			"doc": doc,
			"canvas": canvas,
			"ink_colors": payload.get("ink_colors") or {},
			"lookups": lookups,
			"options": options,
			"safety": safety,
		}


def resolve_db_template_calls(html_template, doc, lookups):
	"""
	Resolve `frappe.get_value(...)` calls in template text using local lookup maps.

	Supported shape:
	lookups = {
		"Raw Material": {
			"CABLMUES14-00001": {"description": "..."}
		}
	}
	"""
	unresolved = []
	resolved_count = 0

	def _replace(match):
		nonlocal resolved_count
		doctype = match.group("doctype")
		name_expr = match.group("name_expr").strip()
		fieldname = match.group("fieldname")

		name_value = _resolve_name_expression(name_expr, doc)
		if not name_value:
			unresolved.append(match.group(0))
			return match.group(0)

		value = _lookup_value(lookups, doctype, str(name_value), fieldname)
		if value is None:
			unresolved.append(match.group(0))
			return match.group(0)

		resolved_count += 1
		return str(value)

	resolved_html = DB_TEMPLATE_CALL_RE.sub(_replace, html_template or "")
	remaining_calls = len(DB_TEMPLATE_CALL_RE.findall(resolved_html))
	return resolved_html, {
		"resolved": resolved_count,
		"remaining_calls": remaining_calls,
		"unresolved": unresolved,
	}


def _resolve_name_expression(name_expr, doc):
	if not name_expr:
		return None

	name_expr = name_expr.strip()
	if (name_expr.startswith("'") and name_expr.endswith("'")) or (
		name_expr.startswith('"') and name_expr.endswith('"')
	):
		return name_expr[1:-1]

	if name_expr.startswith("doc."):
		return _resolve_doc_path(doc, name_expr[4:])

	return None


def _resolve_doc_path(doc, path):
	current = doc
	for part in path.split("."):
		if isinstance(current, dict):
			current = current.get(part)
		else:
			current = getattr(current, part, None)
		if current is None:
			return None
	return current


def _lookup_value(lookups, doctype, name, fieldname):
	doctype_rows = lookups.get(doctype, {}) if isinstance(lookups, dict) else {}
	if not isinstance(doctype_rows, dict):
		return None
	row = doctype_rows.get(name, {})
	if not isinstance(row, dict):
		return None
	return row.get(fieldname)
