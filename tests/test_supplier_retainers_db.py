"""Real-controller retainer integration contracts; explicit DEV runner only.

Every fixture is transaction-local; do not run through a production test runner.
Raw inserts below only construct synthetic Supplier/Item/User fixtures. Agreement,
Batch and Purchase Invoice business operations use their installed controllers.
"""
import json
import os
import unittest
from datetime import date, timedelta
from uuid import uuid4
from unittest.mock import patch

ENABLED = os.environ.get('POWERPRO_RETAINER_DEV_TESTS') == '1'
if ENABLED:
    import frappe
    from frappe.utils import getdate
    from powerpro.retainers import service

AGREEMENT = 'Supplier Retainer Agreement'
BATCH = 'Supplier Retainer Batch'
CLAIM = 'Supplier Retainer Claim'


@unittest.skipUnless(ENABLED, 'Use the exact-site rollback-only development runner')
class SupplierRetainerDatabaseTest(unittest.TestCase):
    def setUp(self):
        self.original_user = frappe.session.user
        frappe.set_user('Administrator')
        self.point = 'retainer_test_' + uuid4().hex
        frappe.db.savepoint(self.point)
        self.addCleanup(self.cleanup)
        self.suffix = uuid4().hex[:12]
        self.company = os.environ['POWERPRO_RETAINER_TEST_COMPANY']
        self.currency = frappe.db.get_value('Company', self.company, 'default_currency')
        self.center = frappe.db.get_value('Cost Center', {'company': self.company, 'is_group': 0, 'disabled': 0}, 'name')
        self.expense = frappe.db.get_value('Account', {'company': self.company, 'is_group': 0, 'disabled': 0, 'root_type': 'Expense', 'account_currency': self.currency}, 'name')
        self.tax_account = frappe.db.get_value('Account', {'company': self.company, 'is_group': 0, 'disabled': 0, 'root_type': 'Liability', 'account_type': ['!=', 'Payable'], 'account_currency': self.currency}, 'name')
        self.assertTrue(self.currency and self.center and self.expense and self.tax_account, 'Company requires a currency, leaf cost center, expense and non-payable liability account.')
        self.today = getdate()
        self.period = self.today.replace(day=1)
        self.employee_count = frappe.db.count('Employee')
        self.gl_count = frappe.db.count('GL Entry')
        self.supplier = self.raw('Supplier', 'RT-SUP-' + self.suffix,
            supplier_name='Rollback Retainer Supplier ' + self.suffix,
            supplier_type='Individual', disabled=0,
            supplier_group=frappe.db.get_value('Supplier Group', {'is_group': 0}, 'name'),
            default_currency=self.currency)
        self.uom = frappe.db.get_value('UOM', {}, 'name')
        self.assertTrue(self.uom, 'An existing UOM is required.')
        self.item = self.raw('Item', 'RT-SVC-' + self.suffix,
            item_code='RT-SVC-' + self.suffix, item_name='Rollback retainer service',
            item_group=frappe.db.get_value('Item Group', {'is_group': 0}, 'name'),
            stock_uom=self.uom, is_stock_item=0, is_purchase_item=1,
            is_sales_item=0, disabled=0, item_type='Servicios')
        self.template = self.tax_template(15)
        self.other_company = self.raw('Company', 'RT-CO-' + self.suffix,
            company_name='Rollback comparison company ' + self.suffix,
            abbr='RT' + self.suffix[:5], default_currency=self.currency,
            country='Dominican Republic')

    def cleanup(self):
        frappe.db.rollback(save_point=self.point)
        frappe.set_user(self.original_user)

    def raw(self, doctype, name, **values):
        doc = frappe.new_doc(doctype)
        doc.update(values)
        doc.name = name
        doc.db_insert()
        return doc

    def tax_template(self, rate, company=None):
        template = frappe.get_doc(dict(
            doctype='Purchase Taxes and Charges Template',
            title='Rollback retainer ' + str(rate) + ' ' + uuid4().hex[:10],
            company=company or self.company,
            taxes=[dict(charge_type='On Net Total', account_head=self.tax_account,
                description='Synthetic withholding test fixture', rate=rate,
                add_deduct_tax='Deduct', category='Total', cost_center=self.center)]))
        template.insert(ignore_permissions=True)
        return template

    def agreement(self, **changes):
        values = dict(doctype=AGREEMENT, title='Rollback agreement ' + uuid4().hex[:10], supplier=self.supplier.name, company=self.company,
            item=self.item.name, gross_amount=50000, currency=self.currency,
            frequency='Monthly', start_date=date(self.today.year, 1, 1),
            end_date=date(self.today.year + 1, 12, 31),
            expense_account=self.expense, cost_center=self.center,
            taxes_and_charges=self.template.name)
        values.update(changes)
        doc = frappe.get_doc(values)
        doc.insert()
        doc.submit()
        return doc

    def batch(self, agreements, period=None, submit=True, **changes):
        values = dict(doctype=BATCH, company=self.company, currency=self.currency,
            frequency='Monthly', period_date=period or self.period,
            posting_date=self.today, details=[dict(agreement=d.name) for d in agreements])
        values.update(changes)
        batch = frappe.get_doc(values)
        batch.insert()
        if submit:
            batch.submit()
            batch.reload()
        return batch

    def invoice(self, batch):
        self.assertEqual(len(batch.details), 1)
        self.assertTrue(batch.details[0].purchase_invoice)
        return frappe.get_doc('Purchase Invoice', batch.details[0].purchase_invoice)

    def test_supplier_only_real_draft_invoice_with_deduction(self):
        agreement = self.agreement()
        batch = self.batch([agreement])
        invoice = self.invoice(batch)
        self.assertEqual((batch.docstatus, invoice.docstatus), (1, 0))
        self.assertEqual(invoice.supplier, self.supplier.name)
        self.assertEqual(invoice.company, self.company)
        self.assertEqual(float(invoice.net_total), 50000)
        self.assertEqual(float(invoice.grand_total), 42500)
        self.assertEqual(invoice.taxes_and_charges, self.template.name)
        self.assertEqual(invoice.taxes[0].add_deduct_tax, 'Deduct')
        self.assertEqual(float(invoice.taxes[0].rate), 15)
        self.assertEqual(frappe.db.count('Employee'), self.employee_count)
        self.assertEqual(frappe.db.count('GL Entry'), self.gl_count)
        self.assertFalse(invoice.get('ncf'), 'Draft generation must not issue a fiscal document.')
        self.assertEqual(frappe.db.count(CLAIM, {'agreement': agreement.name}), 1)

    def test_duplicate_batch_blocked_while_first_invoice_is_draft(self):
        agreement = self.agreement()
        first = self.batch([agreement])
        before = frappe.db.count('Purchase Invoice')
        with self.assertRaises(frappe.ValidationError):
            self.batch([agreement])
        self.assertEqual(frappe.db.count('Purchase Invoice'), before)
        self.assertEqual(self.invoice(first).docstatus, 0)

    def test_two_services_same_supplier_are_independently_billable(self):
        one, two = self.agreement(), self.agreement()
        batch = self.batch([one, two])
        self.assertEqual(len({row.purchase_invoice for row in batch.details}), 2)
        self.assertEqual(frappe.db.count('Employee'), self.employee_count)

    def test_template_change_only_affects_future_generated_invoice(self):
        agreement = self.agreement()
        first_invoice = self.invoice(self.batch([agreement]))
        next_template = self.tax_template(10)
        agreement.taxes_and_charges = next_template.name
        agreement.save()
        next_period = (self.period.replace(day=28) + timedelta(days=4)).replace(day=1)
        later_invoice = self.invoice(self.batch([agreement], period=next_period))
        first_invoice.reload()
        self.assertEqual((float(first_invoice.grand_total), float(later_invoice.grand_total)), (42500, 45000))
        self.assertEqual(first_invoice.taxes_and_charges, self.template.name)
        self.assertEqual(later_invoice.taxes_and_charges, next_template.name)

    def test_optional_template_enforcement_uses_invoice_generation_snapshot(self):
        agreement = self.agreement()
        invoice = self.invoice(self.batch([agreement]))
        alternative = self.tax_template(10)
        frappe.db.set_single_value('Power-Pro Settings', 'enforce_retainer_tax_template', 1)
        agreement.taxes_and_charges = alternative.name
        agreement.save()
        # An agreement's new selection does not invalidate already generated bills.
        invoice.remarks = 'Unrelated draft edit after agreement template change'
        invoice.save()
        self.assertEqual(invoice.custom_supplier_retainer_tax_template, self.template.name)
        invoice.taxes_and_charges = alternative.name
        with self.assertRaises(frappe.ValidationError):
            invoice.save()
        frappe.db.set_single_value('Power-Pro Settings', 'enforce_retainer_tax_template', 0)
        invoice.reload()
        invoice.taxes_and_charges = alternative.name
        invoice.save()
        self.assertEqual(invoice.taxes_and_charges, alternative.name)
        self.assertEqual(invoice.custom_supplier_retainer_tax_template, self.template.name)

    def test_submitted_agreement_amount_is_protected(self):
        agreement = self.agreement()
        agreement.gross_amount = 60000
        with self.assertRaises(frappe.ValidationError):
            agreement.save()
        self.assertEqual(float(frappe.db.get_value(AGREEMENT, agreement.name, 'gross_amount')), 50000)

    def test_direct_invoice_source_and_forged_generation_flags_rejected(self):
        from powerpro.retainers.invoice_hooks import SOURCE_FIELDS
        source = self.invoice(self.batch([self.agreement()]))
        forged = frappe.copy_doc(source)
        for field in SOURCE_FIELDS:
            forged.set(field, source.get(field))
        forged.flags.retainer_service = True
        forged.flags.from_retainer_batch = True
        forged.flags.supplier_retainer_generation = True
        before = frappe.db.count('Purchase Invoice')
        with self.assertRaisesRegex(frappe.ValidationError, 'Liquidaci|iguala'):
            forged.insert()
        self.assertEqual(frappe.db.count('Purchase Invoice'), before)

    def test_ordinary_invoice_unaffected_by_retainer_enforcement(self):
        from powerpro.retainers.invoice_hooks import SOURCE_FIELDS
        source = self.invoice(self.batch([self.agreement()]))
        ordinary = frappe.copy_doc(source)
        for field in SOURCE_FIELDS:
            ordinary.set(field, None)
        frappe.db.set_single_value('Power-Pro Settings', 'enforce_retainer_tax_template', 1)
        ordinary.insert()
        self.assertEqual(ordinary.docstatus, 0)
        self.assertFalse(ordinary.get('custom_supplier_retainer_claim'))
        self.assertEqual(float(ordinary.grand_total), 42500)
        self.assertEqual(frappe.db.count('GL Entry'), self.gl_count)

    def test_client_cannot_supply_generated_invoice_link(self):
        agreement = self.agreement()
        before = frappe.db.count('Purchase Invoice')
        with self.assertRaises(frappe.ValidationError):
            self.batch([agreement], details=[dict(agreement=agreement.name, purchase_invoice='FORGED-INVOICE')])
        self.assertEqual(frappe.db.count('Purchase Invoice'), before)

    def test_generated_invoice_cannot_lose_source_or_be_deleted(self):
        invoice = self.invoice(self.batch([self.agreement()]))
        original_claim = invoice.custom_supplier_retainer_claim
        invoice.custom_supplier_retainer_claim = None
        with self.assertRaises(frappe.ValidationError):
            invoice.save()
        self.assertEqual(frappe.db.get_value('Purchase Invoice', invoice.name, 'custom_supplier_retainer_claim'), original_claim)
        with self.assertRaises(frappe.ValidationError):
            frappe.delete_doc('Purchase Invoice', invoice.name)
        self.assertTrue(frappe.db.exists('Purchase Invoice', invoice.name))

    def assert_batch_invoices_unchanged(self, batch, invoice_names):
        batch.reload()
        self.assertEqual(batch.docstatus, 1)
        self.assertEqual([row.purchase_invoice for row in batch.details], invoice_names)
        for name in invoice_names:
            self.assertTrue(frappe.db.exists('Purchase Invoice', name))
            claim_name = frappe.db.get_value('Purchase Invoice', name, 'custom_supplier_retainer_claim')
            self.assertEqual(frappe.db.get_value(CLAIM, claim_name, 'purchase_invoice'), name)

    def test_cancel_batch_removes_drafts_preserves_audit_and_releases_exact_period(self):
        agreement = self.agreement()
        batch = self.batch([agreement])
        invoice = self.invoice(batch)
        claim_name = invoice.custom_supplier_retainer_claim
        batch.cancel()
        batch.reload()
        self.assertEqual(batch.docstatus, 2)
        self.assertFalse(batch.details[0].purchase_invoice)
        self.assertFalse(frappe.db.exists('Purchase Invoice', invoice.name))
        claim = frappe.get_doc(CLAIM, claim_name)
        self.assertFalse(claim.purchase_invoice)
        self.assertEqual(claim.batch, batch.name)
        self.assertEqual(claim.agreement_identity, agreement.name)
        deleted = frappe.get_all('Deleted Document', filters={
            'deleted_doctype': 'Purchase Invoice', 'deleted_name': invoice.name}, fields=['data'])
        self.assertEqual(len(deleted), 1)
        snapshot = json.loads(deleted[0].data)
        self.assertEqual(snapshot['custom_supplier_retainer_batch'], batch.name)
        self.assertEqual(snapshot['custom_supplier_retainer_claim'], claim_name)
        comments = frappe.get_all('Comment', filters={
            'reference_doctype': BATCH, 'reference_name': batch.name}, pluck='content')
        self.assertTrue(any(invoice.name in (comment or '') for comment in comments))
        next_batch = self.batch([agreement])
        next_invoice = self.invoice(next_batch)
        self.assertNotEqual(next_invoice.name, invoice.name)
        self.assertEqual(next_invoice.custom_supplier_retainer_claim, claim_name)
        self.assertEqual(frappe.db.get_value(CLAIM, claim_name, 'batch'), next_batch.name)
        self.assertEqual(frappe.db.count(CLAIM, {'agreement_identity': agreement.name}), 1)
        self.assertEqual(frappe.db.count('GL Entry'), self.gl_count)
        # The reusable claim now belongs to a new batch, but the cancelled
        # batch remains the durable audit history of its discarded invoice.
        with self.assertRaises(frappe.ValidationError):
            frappe.delete_doc(BATCH, batch.name)
        self.assertTrue(frappe.db.exists(BATCH, batch.name))
        # Cancellation's internal authorization must not leak into later requests.
        with self.assertRaises(frappe.ValidationError):
            frappe.delete_doc('Purchase Invoice', next_invoice.name)

    def test_submitted_invoice_blocks_cancellation_before_any_draft_deletion(self):
        batch = self.batch([self.agreement(), self.agreement()])
        names = [row.purchase_invoice for row in batch.details]
        # Synthetic status only: no invoice submission or fiscal lifecycle.
        frappe.db.set_value('Purchase Invoice', names[1], 'docstatus', 1)
        with patch.object(frappe, 'delete_doc', wraps=frappe.delete_doc) as deletion:
            with self.assertRaises(frappe.ValidationError):
                batch.cancel()
            deletion.assert_not_called()
        self.assert_batch_invoices_unchanged(batch, names)

    def test_fiscal_draft_blocks_cancellation_before_any_draft_deletion(self):
        # encf_status is a virtual HTML field on this installed Nubef schema;
        # its defensive runtime guard is covered by the isolated hook tests.
        for field, value in (('ncf', 'E410000000001'),
                ('ncf_status', 'Pending DGII Response')):
            with self.subTest(field=field):
                batch = self.batch([self.agreement(), self.agreement()])
                names = [row.purchase_invoice for row in batch.details]
                self.assertTrue(frappe.get_meta('Purchase Invoice').has_field(field),
                    'This fiscal integration contract requires the installed Nubef fields.')
                frappe.db.set_value('Purchase Invoice', names[1], field, value)
                with patch.object(frappe, 'delete_doc', wraps=frappe.delete_doc) as deletion:
                    with self.assertRaises(frappe.ValidationError):
                        batch.cancel()
                    deletion.assert_not_called()
                self.assert_batch_invoices_unchanged(batch, names)

    def test_attached_file_blocks_cancellation_before_any_draft_deletion(self):
        batch = self.batch([self.agreement(), self.agreement()])
        names = [row.purchase_invoice for row in batch.details]
        # A transaction-local metadata fixture only: no download, file write or
        # File controller side effects are needed to exercise the preflight.
        attached_name = sorted(names)[-1]
        attachment = self.raw('File', 'RT-FILE-' + self.suffix,
            file_name='retainer-review.pdf',
            file_url='https://example.invalid/retainer-review.pdf',
            attached_to_doctype='Purchase Invoice', attached_to_name=attached_name,
            is_private=1)
        with patch.object(frappe, 'delete_doc', wraps=frappe.delete_doc) as deletion:
            with self.assertRaises(frappe.ValidationError):
                batch.cancel()
            deletion.assert_not_called()
        self.assert_batch_invoices_unchanged(batch, names)
        self.assertEqual(frappe.db.get_value('File', attachment.name,
            ['attached_to_doctype', 'attached_to_name', 'file_url']),
            ('Purchase Invoice', attached_name, 'https://example.invalid/retainer-review.pdf'))
        self.assertEqual(frappe.db.count('Deleted Document', {
            'deleted_doctype': 'Purchase Invoice', 'deleted_name': ['in', names]}), 0)

    def test_later_delete_failure_restores_invoices_claims_links_and_audit(self):
        batch = self.batch([self.agreement(), self.agreement()])
        names = [row.purchase_invoice for row in batch.details]
        comment_count = frappe.db.count('Comment', {'reference_doctype': BATCH, 'reference_name': batch.name})
        original_delete = frappe.delete_doc
        calls = []

        def fail_second(doctype, name=None, *args, **kwargs):
            if doctype == 'Purchase Invoice' and name in names:
                calls.append(name)
                if len(calls) == 2:
                    self.assertFalse(frappe.db.exists('Purchase Invoice', calls[0]))
                    raise RuntimeError('Injected second draft deletion failure')
            return original_delete(doctype, name, *args, **kwargs)

        with patch.object(frappe, 'delete_doc', fail_second):
            with self.assertRaisesRegex(RuntimeError, 'second draft deletion failure'):
                batch.cancel()
        self.assertEqual(len(calls), 2)
        self.assert_batch_invoices_unchanged(batch, names)
        self.assertEqual(frappe.db.count('Comment', {'reference_doctype': BATCH, 'reference_name': batch.name}), comment_count)
        self.assertEqual(frappe.db.count('Deleted Document', {
            'deleted_doctype': 'Purchase Invoice', 'deleted_name': ['in', names]}), 0)
        # Also prove the authorization context is reset when deletion raises.
        with self.assertRaises(frappe.ValidationError):
            original_delete('Purchase Invoice', names[0])

    def test_invoice_delete_permission_required_to_cancel_batch_with_drafts(self):
        batch = self.batch([self.agreement()])
        names = [row.purchase_invoice for row in batch.details]
        from frappe.model.document import Document
        original_permission = Document.check_permission

        def deny_invoice_delete(doc, permtype='read', *args, **kwargs):
            if doc.doctype == 'Purchase Invoice' and permtype == 'delete':
                raise frappe.PermissionError('Synthetic denial of Purchase Invoice delete permission')
            return original_permission(doc, permtype, *args, **kwargs)

        with patch.object(Document, 'check_permission', deny_invoice_delete):
            with self.assertRaises(frappe.PermissionError):
                batch.cancel()
        self.assert_batch_invoices_unchanged(batch, names)

    def test_cancelled_invoice_kept_when_cancelling_batch(self):
        agreement = self.agreement()
        batch = self.batch([agreement])
        invoice = self.invoice(batch)
        frappe.db.set_value('Purchase Invoice', invoice.name, 'docstatus', 2)
        batch.cancel()
        batch.reload()
        self.assertEqual(batch.docstatus, 2)
        self.assertEqual(batch.details[0].purchase_invoice, invoice.name)
        self.assertEqual(frappe.db.get_value(CLAIM, invoice.custom_supplier_retainer_claim, 'purchase_invoice'), invoice.name)
        self.assertEqual(frappe.db.get_value('Purchase Invoice', invoice.name, 'docstatus'), 2)
        with self.assertRaises(frappe.ValidationError):
            self.batch([agreement])

    def test_released_period_is_reused_through_original_agreement_identity(self):
        agreement = self.agreement()
        batch = self.batch([agreement])
        invoice = self.invoice(batch)
        claim_name = invoice.custom_supplier_retainer_claim
        batch.cancel()
        agreement.cancel()
        amended = frappe.copy_doc(agreement)
        amended.docstatus = 0
        amended.amended_from = agreement.name
        amended.insert()
        amended.submit()
        replacement = self.batch([amended])
        replacement_invoice = self.invoice(replacement)
        self.assertEqual(replacement_invoice.custom_supplier_retainer_claim, claim_name)
        claim = frappe.get_doc(CLAIM, claim_name)
        self.assertEqual(claim.agreement, amended.name)
        self.assertEqual(claim.agreement_identity, agreement.name)
        with self.assertRaises(frappe.ValidationError):
            self.batch([amended])

    def test_active_invoice_cannot_be_explicitly_replaced(self):
        agreement = self.agreement()
        invoice = self.invoice(self.batch([agreement]))
        batch = self.batch([agreement], submit=False)
        batch.details[0].replaces_invoice = invoice.name
        batch.save()
        before = frappe.db.count('Purchase Invoice')
        with self.assertRaises(frappe.ValidationError):
            batch.submit()
        self.assertEqual(frappe.db.count('Purchase Invoice'), before)

    def test_amended_agreement_cannot_rebill_or_overlap_existing_period(self):
        agreement = self.agreement()
        invoice = self.invoice(self.batch([agreement]))
        agreement.cancel()
        amended = frappe.copy_doc(agreement)
        amended.docstatus = 0
        amended.amended_from = agreement.name
        amended.insert()
        amended.submit()
        with self.assertRaises(frappe.ValidationError):
            self.batch([amended])
        # Cancelling and changing frequency cannot turn a previously billed month
        # into a second payable half-month through a different claim key.
        amended.cancel()
        half = frappe.copy_doc(amended)
        half.docstatus = 0
        half.amended_from = amended.name
        half.frequency = 'Bimonthly'
        half.insert()
        half.submit()
        with self.assertRaises(frappe.ValidationError):
            self.batch([half], frequency='Bimonthly')
        invoice.remarks = 'Historical source agreement was amended'
        invoice.save()
        self.assertEqual(invoice.docstatus, 0)
        self.assertEqual(frappe.db.count(CLAIM, {'agreement_identity': agreement.name}), 1)

    def test_duplicate_rows_rejected(self):
        agreement = self.agreement()
        with self.assertRaises(frappe.ValidationError):
            self.batch([agreement, agreement])

    def test_company_mismatch_rejected(self):
        agreement = self.agreement()
        other = self.other_company.name
        with self.assertRaises(frappe.ValidationError):
            self.batch([agreement], company=other)

    def test_currency_mismatch_rejected(self):
        agreement = self.agreement()
        other = frappe.db.get_value('Currency', {'name': ['!=', self.currency], 'enabled': 1}, 'name')
        self.assertTrue(other, 'A second enabled currency is required.')
        with self.assertRaises(frappe.ValidationError):
            self.batch([agreement], currency=other)

    def test_disabled_expense_account_rejected_at_generation(self):
        agreement = self.agreement()
        batch = self.batch([agreement], submit=False)
        frappe.db.set_value('Account', self.expense, 'disabled', 1)
        with self.assertRaises(frappe.ValidationError):
            batch.submit()
        self.assertFalse(frappe.db.exists(CLAIM, {'agreement': agreement.name}))

    def test_cross_company_template_rejected(self):
        other = self.other_company.name
        # Mutating this synthetic template only bypasses template validation to
        # verify the Agreement performs its own company check.
        frappe.db.set_value('Purchase Taxes and Charges Template', self.template.name, 'company', other)
        with self.assertRaises(frappe.ValidationError):
            self.agreement()

    def test_second_invoice_failure_rolls_back_first_invoice_and_claims(self):
        agreements = [self.agreement(), self.agreement()]
        batch = self.batch(agreements, submit=False)
        before = frappe.db.count('Purchase Invoice')
        from frappe.model.document import Document
        original_insert = Document.insert
        calls = []

        def failing_insert(doc, *args, **kwargs):
            if doc.doctype == 'Purchase Invoice':
                calls.append(doc.supplier)
                if len(calls) == 2:
                    raise RuntimeError('Injected second invoice failure')
            return original_insert(doc, *args, **kwargs)

        with patch.object(Document, 'insert', failing_insert):
            with self.assertRaisesRegex(RuntimeError, 'second invoice failure'):
                batch.submit()
        self.assertEqual(len(calls), 2, 'Test must fail after the first real invoice insert.')
        self.assertEqual(frappe.db.count('Purchase Invoice'), before)
        for agreement in agreements:
            self.assertFalse(frappe.db.exists(CLAIM, {'agreement': agreement.name}))
        self.assertEqual(frappe.db.get_value(BATCH, batch.name, 'docstatus'), 0)

    def test_calendar_half_periods_generate_separately(self):
        agreement = self.agreement(frequency='Bimonthly')
        first = self.batch([agreement], period=self.period, frequency='Bimonthly')
        second = self.batch([agreement], period=self.period.replace(day=16), frequency='Bimonthly')
        self.assertNotEqual(self.invoice(first).name, self.invoice(second).name)
        self.assertEqual(getdate(first.period_end).day, 15)
        self.assertEqual(getdate(second.period_start).day, 16)
        with self.assertRaises(frappe.ValidationError):
            self.batch([agreement], period=self.period.replace(day=12), frequency='Bimonthly')

    def test_partial_validity_rejected_without_implicit_proration(self):
        agreement = self.agreement(start_date=self.period.replace(day=2))
        with self.assertRaises(frappe.ValidationError):
            self.batch([agreement])

    def test_unprivileged_user_cannot_change_template(self):
        agreement = self.agreement()
        alternative = self.tax_template(10)
        user = self.raw('User', 'retainer-' + self.suffix + '@example.invalid',
            email='retainer-' + self.suffix + '@example.invalid',
            first_name='Rollback retainer viewer', enabled=1, user_type='System User')
        role = user.append('roles', dict(role='Accounts User'))
        role.db_insert()
        frappe.set_user(user.name)
        agreement = frappe.get_doc(AGREEMENT, agreement.name)
        agreement.taxes_and_charges = alternative.name
        with self.assertRaises((frappe.PermissionError, frappe.ValidationError)):
            agreement.save()
        self.assertEqual(frappe.db.get_value(AGREEMENT, agreement.name, 'taxes_and_charges'), self.template.name)

    def test_invoice_cancel_link_guard_ignores_only_retainer_audit_links(self):
        from inspect import signature
        from frappe.model.delete_doc import check_if_doc_is_linked
        from powerpro.retainers.invoice_hooks import before_cancel
        self.assertIn('method', signature(check_if_doc_is_linked).parameters)
        agreement = self.agreement()
        batch = self.batch([agreement])
        invoice = self.invoice(batch)
        # Simulate the status needed by Frappe's link checker on this synthetic
        # invoice; no submit/cancel controller or fiscal lifecycle is invoked.
        frappe.db.set_value('Purchase Invoice', invoice.name, 'docstatus', 1)
        invoice.reload()
        invoice._doc_before_save = frappe.get_doc('Purchase Invoice', invoice.name)
        with self.assertRaises(frappe.LinkExistsError):
            check_if_doc_is_linked(invoice, method='Cancel')
        before_cancel(invoice)
        check_if_doc_is_linked(invoice, method='Cancel')
        self.assertEqual(set(invoice.ignore_linked_doctypes), {CLAIM, BATCH})
        self.assertEqual(frappe.db.count(CLAIM, {'purchase_invoice': invoice.name}), 1)
        self.assertEqual(frappe.db.count('Supplier Retainer Batch Detail', {'purchase_invoice': invoice.name}), 1)
        self.assertEqual(frappe.db.get_value('Purchase Invoice', invoice.name, 'docstatus'), 1)
        self.assertEqual(frappe.db.count('GL Entry'), self.gl_count)

    def test_cancelled_invoice_needs_explicit_replacement(self):
        agreement = self.agreement()
        invoice = self.invoice(self.batch([agreement]))
        # Never submit/cancel fiscal invoices in this runner. Only this synthetic
        # draft's stored status is changed to exercise the replacement contract;
        # fiscal cancellation lifecycle is a separate integration gate.
        frappe.db.set_value('Purchase Invoice', invoice.name, 'docstatus', 2)
        with self.assertRaises(frappe.ValidationError):
            self.batch([agreement])
        replacement = self.batch([agreement], submit=False)
        replacement.details[0].replaces_invoice = invoice.name
        replacement.save()
        replacement.submit()
        replacement.reload()
        self.assertNotEqual(self.invoice(replacement).name, invoice.name)
        self.assertEqual(frappe.db.get_value('Purchase Invoice', invoice.name, 'docstatus'), 2)


if __name__ == '__main__':
    unittest.main()
