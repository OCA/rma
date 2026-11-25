# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tools import mute_logger

from odoo.addons.rma_inter_company.tests.common import TestRmaInterCompanyBase


class TestRmaInterCompanyDropshipping(TestRmaInterCompanyBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # In an inter-company context, the drop_shipping route is not required for all
        # companies, only for Company A; therefore, we simulate the manual
        # configuration we would perform
        cls.dropshipping_route = cls.env.ref(
            "stock_dropshipping.route_drop_shipping", raise_if_not_found=False
        )
        if not cls.dropshipping_route:
            return
        cls.dropshipping_route.rule_ids.filtered(
            lambda x: x.company_id != cls.company_a
        ).unlink()
        cls.dropshipping_route.company_id = cls.company_a
        cls.product.write(
            {
                "route_ids": [Command.link(cls.dropshipping_route.id)],
            }
        )
        cls._update_available_quantity(cls.product, cls.warehouse_b.lot_stock_id, 1)
        cls.so_a.action_confirm()
        # Confirm PO Company A
        cls.po_a = cls.so_a._get_purchase_orders()
        cls.po_a.button_confirm()
        cls.so_a_picking = cls.po_a_picking = cls.po_a.picking_ids
        # Confirm SO Company B
        cls.so_b = cls.po_a.intercompany_sale_order_id
        cls.so_b_picking = cls.so_b.picking_ids
        # Validate OUT SO Company B
        cls.so_b_picking.button_validate()
        # Validate IN PO Company B
        cls.po_a_picking.button_validate()

    def test_misc_rma_intercompany_data(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_misc_rma_intercompany_data()

    def test_rma_intercompany_sync(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_sync()

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_from_so_company_b(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_from_so_company_b()

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_cancel_company_b(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_cancel_company_b()

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_cancel_company_a(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_cancel_company_a()

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_return_cancel_company_a(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_return_cancel_company_a()

    def test_rma_intercompany_reception_company_b(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_reception_company_b()

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_return_cancel_company_b(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_return_cancel_company_b()

    def test_rma_intercompany_full_company_b(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_full_company_b()

    def test_rma_intercompany_full_company_a(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_full_company_a()

    def test_rma_intercompany_replace_full_company_b(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_replace_full_company_b()

    def test_rma_intercompany_replace_full_company_a(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_replace_full_company_a()

    def test_rma_intercompany_new_rma_company_a(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_new_rma_company_a()

    def test_rma_intercompany_new_rma_company_b(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_new_rma_company_b()

    def test_rma_intercompany_refund_without_invoice_company_a(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_refund_without_invoice_company_a()

    def test_rma_intercompany_refund_without_invoice_a_with_invoice_b(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_refund_without_invoice_a_with_invoice_b()

    def test_rma_intercompany_refund_without_invoice_company_b(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_refund_without_invoice_company_b()

    def test_rma_intercompany_refund_without_invoice_b_with_invoice_a(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_refund_without_invoice_b_with_invoice_a()

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_refund_company_a_full(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_refund_company_a_full()

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_refund_with_invoice_a_without_invoice_b(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_refund_with_invoice_a_without_invoice_b()

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_refund_company_b_full(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_refund_company_b_full()

    @mute_logger("odoo.models.unlink")
    def test_rma_intercompany_refund_with_invoice_b_without_invoice_a(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_intercompany_refund_with_invoice_b_without_invoice_a()

    def test_rma_not_intercompany_company_a(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_not_intercompany_company_a()

    def test_rma_not_intercompany_company_b(self):
        if not self.dropshipping_route:
            self.skipTest("stock_dropshipping is not installed")
        self._test_rma_not_intercompany_company_b()
