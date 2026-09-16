"""Invoice provenance and optional template guard contracts without Frappe."""
from datetime import date
from html import escape
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
frappe = ModuleType('frappe')
frappe._ = lambda value: value


def throw(message):
    raise ValueError(message)


frappe.throw = throw
frappe.db = SimpleNamespace(get_single_value=lambda *args: 0, get_value=lambda *args: None)
utils = ModuleType('frappe.utils')
utils.cint = lambda value: int(value or 0)
utils.getdate = lambda value: value if isinstance(value, date) else date.fromisoformat(value)
utils.escape_html = escape
cancellation_spec = importlib.util.spec_from_file_location(
    'powerpro.retainers.cancellation', ROOT / 'powerpro/retainers/cancellation.py')
cancellation = importlib.util.module_from_spec(cancellation_spec)
spec = importlib.util.spec_from_file_location('retainer_invoice_hooks', ROOT / 'powerpro/retainers/invoice_hooks.py')
hooks = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {'frappe': frappe, 'frappe.utils': utils}):
    cancellation_spec.loader.exec_module(cancellation)
    spec.loader.exec_module(hooks)


class Doc(dict):
    def __init__(self, *args, previous=None, new=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.previous, self.new = previous, new
        self.meta = SimpleNamespace(has_field=lambda name: True)

    def get_doc_before_save(self):
        return self.previous

    def is_new(self):
        return self.new

    def __getattr__(self, name):
        return self.get(name)


class RetainerInvoiceHookTest(unittest.TestCase):
    def setUp(self):
        modules = patch.dict(sys.modules, {'powerpro.retainers.cancellation': cancellation})
        modules.start()
        self.addCleanup(modules.stop)

    def linked(self, **changes):
        values = dict(custom_supplier_retainer_claim='claim', custom_supplier_retainer_agreement='agreement',
            custom_supplier_retainer_batch='batch', custom_supplier_retainer_period_start='2026-09-01',
            custom_supplier_retainer_period_end='2026-09-30', custom_supplier_retainer_tax_template='original',
            taxes_and_charges='original', supplier='Supplier', company='Company', currency='DOP')
        values.update(changes)
        return values

    def test_only_internal_generation_context_assigns_provenance(self):
        doc = Doc(self.linked(), new=True)
        with self.assertRaises(ValueError):
            hooks.validate_source(doc)
        with hooks.generating_invoice('batch', 'agreement', 'claim'):
            hooks.validate_source(doc)
        with self.assertRaises(ValueError):
            hooks.validate_source(doc)

    def test_generation_context_resets_after_exception(self):
        with self.assertRaises(RuntimeError):
            with hooks.generating_invoice('batch', 'agreement', 'claim'):
                raise RuntimeError('insertion failed')
        with self.assertRaises(ValueError):
            hooks.validate_source(Doc(self.linked(), new=True))

    def test_source_and_party_fields_are_immutable(self):
        previous = Doc(self.linked())
        for field in hooks.SOURCE_FIELDS + ('supplier', 'company', 'currency'):
            changed = self.linked()
            changed[field] = None
            with self.subTest(field=field), self.assertRaises(ValueError):
                hooks.validate_source(Doc(changed, previous=previous))

    def test_equivalent_date_values_are_allowed(self):
        previous = Doc(self.linked())
        doc = Doc(self.linked(custom_supplier_retainer_period_start=date(2026, 9, 1)), previous=previous)
        hooks.validate_source(doc)

    def test_enabled_guard_compares_saved_generation_template(self):
        previous = Doc(self.linked())
        with patch.object(frappe.db, 'get_single_value', return_value=1):
            hooks.validate_source(Doc(self.linked(), previous=previous))
            with self.assertRaises(ValueError):
                hooks.validate_source(Doc(self.linked(taxes_and_charges='new'), previous=previous))

    def test_disabled_guard_allows_draft_template_change(self):
        hooks.validate_source(Doc(self.linked(taxes_and_charges='new'), previous=Doc(self.linked())))

    def test_ordinary_invoice_does_not_query_optional_setting(self):
        with patch.object(frappe.db, 'get_single_value', side_effect=AssertionError('ordinary invoice queried retainer setting')):
            hooks.validate_source(Doc(taxes_and_charges='ordinary', new=True))

    def test_cancelled_retainer_amendment_must_use_batch(self):
        with patch.object(frappe.db, 'get_value', return_value='old-claim'):
            with self.assertRaises(ValueError):
                hooks.validate_source(Doc(amended_from='cancelled-invoice', new=True))

    def test_cancellation_allows_historical_alternate_template_but_protects_source(self):
        previous = Doc(self.linked(taxes_and_charges='historical', docstatus=1))
        cancelled = Doc(self.linked(taxes_and_charges='historical', docstatus=2), previous=previous)
        with patch.object(frappe.db, 'get_single_value', return_value=1):
            hooks.before_cancel(cancelled)
            self.assertEqual(set(cancelled.ignore_linked_doctypes),
                {'Supplier Retainer Claim', 'Supplier Retainer Batch'})
            cancelled['custom_supplier_retainer_claim'] = None
            with self.assertRaises(ValueError):
                hooks.validate_source(cancelled)

    def test_optional_schema_missing_does_not_block_ordinary_invoice(self):
        doc = Doc(new=True)
        doc.meta = SimpleNamespace(has_field=lambda name: False)
        hooks.validate_source(doc)

    def test_retainer_invoice_delete_blocked_ordinary_allowed(self):
        with self.assertRaises(ValueError):
            hooks.protect_delete(Doc(self.linked()))
        hooks.protect_delete(Doc())

    def test_matching_server_context_allows_only_unissued_draft_deletion(self):
        doc = Doc(self.linked(name='invoice', docstatus=0, ncf_status='Never Sent'))
        with cancellation.discarding_draft('batch', 'invoice'):
            hooks.protect_delete(doc)
        with self.assertRaises(ValueError):
            hooks.protect_delete(doc)

    def test_draft_deletion_context_must_match_invoice_and_batch(self):
        doc = Doc(self.linked(name='invoice', docstatus=0))
        doc.flags = SimpleNamespace(retainer_service=True, discarding_draft=True)
        for batch, invoice in (('other-batch', 'invoice'), ('batch', 'other-invoice')):
            with self.subTest(batch=batch, invoice=invoice):
                with cancellation.discarding_draft(batch, invoice):
                    with self.assertRaises(ValueError):
                        hooks.protect_delete(doc)
        with self.assertRaises(ValueError):
            hooks.protect_delete(doc)

    def test_submitted_and_fiscal_invoices_rejected_even_with_matching_context(self):
        variants = (
            {'docstatus': 1}, {'docstatus': 2},
            {'ncf': 'E410000000001'}, {'encf_status': 'Accepted'},
            {'ncf_status': 'Send Failed (Unconfirmed)'},
            {'ncf_status': 'Pending DGII Response'}, {'ncf_status': 'Rejected'},
            {'ncf_status': 'Rejected (NCF Consumed)'},
            {'ncf_status': 'Legally Accepted'}, {'ncf_status': 'Accepted with Warnings'},
        )
        for values in variants:
            doc = Doc(self.linked(**dict({'name': 'invoice', 'docstatus': 0}, **values)))
            with self.subTest(values=values), cancellation.discarding_draft('batch', 'invoice'):
                with self.assertRaises(ValueError):
                    hooks.protect_delete(doc)

    def test_discard_context_resets_after_exception(self):
        with self.assertRaises(RuntimeError):
            with cancellation.discarding_draft('batch', 'invoice'):
                raise RuntimeError('deletion failed')
        with self.assertRaises(ValueError):
            hooks.protect_delete(Doc(self.linked(name='invoice', docstatus=0)))


if __name__ == '__main__':
    unittest.main()
