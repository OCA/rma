# Copyright 2026 Tecnativa - Juan Carlos Oñate
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from .test_rma_sale import TestRmaSaleBase


class TestRmaSaleRefundFromInvoice(TestRmaSaleBase):
    """The refund of an RMA rectifies an invoice, so it must carry what was
    invoiced instead of what today's configuration would compute.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.operation.action_create_refund = "manual_after_receipt"
        cls.product_1.invoice_policy = "delivery"
        cls.product_tax = cls.env["account.tax"].search(
            [("type_tax_use", "=", "sale"), ("company_id", "=", cls.company.id)],
            limit=1,
        )
        cls.product_1.taxes_id = [Command.set(cls.product_tax.ids)]
        cls.order = cls._create_sale_order([[cls.product_1, 5]])
        cls.order.action_confirm()
        cls.order_line = cls.order.order_line.filtered(
            lambda line: line.product_id == cls.product_1
        )
        picking = cls.order.picking_ids
        picking.move_ids.quantity = 5
        picking.button_validate()
        cls.invoice = cls.order._create_invoices()
        # The invoice deliberately differs from what the product would compute:
        # it is exempt and it is issued in another journal.
        cls.sale_journal = cls.invoice.journal_id.copy(
            {"name": "Other sale journal", "code": "RMAJ2"}
        )
        cls.invoice.journal_id = cls.sale_journal
        cls.invoice.invoice_line_ids.tax_ids = [Command.clear()]
        cls.invoice.action_post()

    def _refund_rma(self, order=None, product=None, quantity=None):
        wizard = self._rma_sale_wizard(order or self.order)
        if quantity is not None:
            wizard.line_ids.quantity = quantity
        rma = self.env["rma"].browse(wizard.create_and_open_rma()["res_id"])
        rma.reception_move_id.quantity = rma.product_uom_qty
        rma.reception_move_id.picking_id.button_validate()
        rma.action_refund()
        refund_line = rma.refund_id.invoice_line_ids.filtered(
            lambda line: line.product_id == (product or self.product_1)
        )
        return rma, refund_line

    def test_refund_derived_from_the_invoice(self):
        self.assertTrue(self.product_tax, "The product must have a default tax")
        rma, refund_line = self._refund_rma()
        invoice_line = self.invoice.invoice_line_ids
        # What was invoiced, not what the product would compute now
        self.assertFalse(refund_line.tax_ids)
        self.assertEqual(refund_line.account_id, invoice_line.account_id)
        self.assertEqual(refund_line.price_unit, invoice_line.price_unit)
        self.assertEqual(rma.refund_id.journal_id, self.sale_journal)
        # The invoice shows it has been rectified, so it is not rectified twice
        self.assertEqual(rma.refund_id.reversed_entry_id, self.invoice)
        self.assertIn(rma.refund_id, self.invoice.reversal_move_ids)
        # The refund line keeps belonging to its RMA
        self.assertEqual(refund_line.rma_id, rma)
        self.assertEqual(rma.refund_line_id, refund_line)

    def test_refund_quantity_comes_from_the_rma(self):
        """The invoice line holds 5 units, the RMA returns 2."""
        dummy, refund_line = self._refund_rma(quantity=2)
        self.assertEqual(refund_line.quantity, 2)
        self.assertFalse(refund_line.tax_ids)

    def test_refund_falls_back_without_a_single_origin_invoice(self):
        """Never derive from a guessed document: no invoice, or several."""
        order = self._create_sale_order([[self.product_2, 3]])
        order.action_confirm()
        picking = order.picking_ids
        picking.move_ids.quantity = 3
        picking.button_validate()
        rma, refund_line = self._refund_rma(order=order, product=self.product_2)
        self.assertFalse(rma.refund_id.reversed_entry_id)
        self.assertEqual(
            refund_line.price_unit,
            order.order_line.filtered(
                lambda line: line.product_id == self.product_2
            ).price_unit,
        )
        # Several candidate invoices for the same sales order line
        second_invoice = self.invoice.copy()
        second_invoice.invoice_line_ids.sale_line_ids = [
            Command.set(self.order_line.ids)
        ]
        second_invoice.action_post()
        self.assertFalse(rma._get_refund_origin_invoice_line(self.order_line))
