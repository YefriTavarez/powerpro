# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import re
import unicodedata

from typing import Any

PARENTHETICAL = re.compile(r"\([^)]*\)")
PT_IN_NAME = re.compile(r"(\d+)\s*pt", re.IGNORECASE)
MEASUREMENT_TOKEN = re.compile(r"^\d+(?:pt|lb|gsm|in|mm)$", re.IGNORECASE)
CODE_TOKEN = re.compile(r"^[A-Za-z]+[0-9]+[A-Za-z0-9]*$")
NON_ALNUM = re.compile(r"[^A-Za-z0-9]")


def strip_diacritics(value: str) -> str:
	normalized = unicodedata.normalize("NFD", value or "")
	return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def extract_pt(item_name: str) -> str:
	match = PT_IN_NAME.search(item_name or "")
	if not match:
		raise ValueError("pt")

	return match.group(1)


def extract_initials(item_name: str) -> str:
	cleaned = PARENTHETICAL.sub(" ", item_name or "")
	parts = []

	for raw_token in cleaned.split():
		token = NON_ALNUM.sub("", strip_diacritics(raw_token))
		if not token or MEASUREMENT_TOKEN.match(token) or token.isdigit():
			continue

		if CODE_TOKEN.match(token):
			parts.append(token.upper())
			continue

		letter = next((char for char in token if char.isalpha()), None)
		if letter:
			parts.append(letter.upper())

	if not parts:
		raise ValueError("initials")

	return "".join(parts)


def build_batch_number_series(item_name: str, gsm: Any) -> str:
	initials = extract_initials(item_name)
	pt = extract_pt(item_name)
	try:
		gsm_value = int(gsm)
	except (TypeError, ValueError):
		gsm_value = 0

	if gsm_value <= 0:
		raise ValueError("gsm")

	return f".YY.MM.DD.-{initials}-{pt}-{gsm_value}-.##."


def get_roll_serial_and_batch_fields(item_name: str, gsm: Any) -> dict:
	import frappe
	from frappe import _

	try:
		series = build_batch_number_series(item_name, gsm)
	except ValueError as exc:
		reason = str(exc)
		if reason == "pt":
			frappe.throw(
				_(
					"No se pudo extraer el calibre (pt) del nombre del artículo '{0}' "
					"para generar la serie de lote."
				).format(item_name)
			)
		if reason == "initials":
			frappe.throw(
				_(
					"No se pudieron generar las iniciales del nombre del artículo '{0}' "
					"para la serie de lote."
				).format(item_name)
			)
		if reason == "gsm":
			frappe.throw(_("El GSM es obligatorio para generar la serie de lote del rollo."))

		frappe.throw(_("No se pudo generar la serie de lote para el rollo."))

	return {
		"has_batch_no": 1,
		"create_new_batch": 1,
		"has_serial_no": 1,
		"batch_number_series": series,
	}
