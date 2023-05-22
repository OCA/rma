# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def _prepare_rma_partner_values(self):
        sale_order = self.picking_id.sale_id
        if not sale_order:
            return super()._prepare_rma_partner_values()
        return (
            sale_order.partner_id,
            sale_order.partner_invoice_id,
            sale_order.partner_shipping_id,
        )

    def _prepare_rma_values(self):
        vals = super()._prepare_rma_values()
        sale_order = self.picking_id.sale_id
        if sale_order:
            vals.update(
                {
                    "order_id": sale_order.id,
                }
            )
        return vals
