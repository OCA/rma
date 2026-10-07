# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tools import mute_logger

from odoo.addons.rma_inter_company.tests.common import TestRmaInterCompanyBase


class TestRmaInterCompanyMto(TestRmaInterCompanyBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mto_route.active = True
        cls.supplier = cls.env["res.partner"].create({"name": "Test supplier"})
        cls.product.write(
            {
                "seller_ids": [
                    Command.create(
                        {
                            "partner_id": cls.supplier.id,
                            "company_id": cls.company_b.id,
                        }
                    ),
                ],
            }
        )
        cls.so_a.action_confirm()
        cls.so_a_picking = cls.so_a.picking_ids
        # Confirm PO Company A
        cls.po_a = cls.so_a._get_purchase_orders()
        cls.po_a.button_confirm()
        cls.po_a_picking = cls.po_a.picking_ids
        cls.so_b = cls.po_a.intercompany_sale_order_id
        cls.po_b = cls.so_b._get_purchase_orders()
        # Confirm PO Company B
        cls.po_b.button_confirm()
        # Validate IN PO Company B
        cls.po_b.picking_ids.button_validate()
        # Validate OUT SO Company B
        cls.so_b_picking = cls.so_b.picking_ids
        # Validate OUT SO Company B
        cls.so_b_picking.button_validate()
        # Validate IN PO Company B
        cls.po_a_picking.button_validate()
        # Validate OUT SO Company A
        cls.so_a_picking.button_validate()

    def test_misc_rma_intercompany_data(self):
        self._test_misc_rma_intercompany_data()

    def test_rma_intercompany_sync(self):
        self._test_rma_intercompany_sync()

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_from_so_company_b(self):
        self._test_rma_intercompany_from_so_company_b()

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_cancel_company_b(self):
        self._test_rma_intercompany_cancel_company_b()

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_cancel_company_a(self):
        self._test_rma_intercompany_cancel_company_a()

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_return_cancel_company_a(self):
        self._test_rma_intercompany_return_cancel_company_a()

    def test_rma_intercompany_reception_company_b(self):
        self._test_rma_intercompany_reception_company_b()

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_return_cancel_company_b(self):
        self._test_rma_intercompany_return_cancel_company_b()

    def test_rma_intercompany_full_company_b(self):
        self._test_rma_intercompany_full_company_b()

    def test_rma_intercompany_full_company_a(self):
        self._test_rma_intercompany_full_company_a()

    def test_rma_intercompany_replace_full_company_b(self):
        self._test_rma_intercompany_replace_full_company_b()

    def test_rma_intercompany_replace_full_company_a(self):
        self._test_rma_intercompany_replace_full_company_a()

    def test_rma_intercompany_new_rma_company_a(self):
        self._test_rma_intercompany_new_rma_company_a()

    def test_rma_intercompany_new_rma_company_b(self):
        self._test_rma_intercompany_new_rma_company_b()

    def test_rma_intercompany_refund_without_invoice_company_a(self):
        self._test_rma_intercompany_refund_without_invoice_company_a()

    def test_rma_intercompany_refund_without_invoice_a_with_invoice_b(self):
        self._test_rma_intercompany_refund_without_invoice_a_with_invoice_b()

    def test_rma_intercompany_refund_without_invoice_company_b(self):
        self._test_rma_intercompany_refund_without_invoice_company_b()

    def test_rma_intercompany_refund_without_invoice_b_with_invoice_a(self):
        self._test_rma_intercompany_refund_without_invoice_b_with_invoice_a()

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_refund_company_a_full(self):
        self._test_rma_intercompany_refund_company_a_full()

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_refund_with_invoice_a_without_invoice_b(self):
        self._test_rma_intercompany_refund_with_invoice_a_without_invoice_b()

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_refund_company_b_full(self):
        self._test_rma_intercompany_refund_company_b_full()

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_refund_with_invoice_b_without_invoice_a(self):
        self._test_rma_intercompany_refund_with_invoice_b_without_invoice_a()

    def test_rma_not_intercompany_company_a(self):
        self._test_rma_not_intercompany_company_a()

    def test_rma_not_intercompany_company_b(self):
        self._test_rma_not_intercompany_company_b()
