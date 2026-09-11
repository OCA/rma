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

    def _prepare_rma_vals(self):
        vals = super()._prepare_rma_vals()
        sale_order = self.picking_id.sale_id
        if sale_order:
            vals["order_id"] = sale_order.id
        return vals


class ReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    def _prepare_rma_vals(self):
        vals = super()._prepare_rma_vals()
        # If the RMA is created from a picking order linked to a sales order, the
        # partner data in the RMA must be correct
        order = self.move_id.sale_line_id.order_id
        if order:
            vals.update(
                partner_id=order.partner_id.id,
                partner_shipping_id=order.partner_shipping_id.id,
                partner_invoice_id=order.partner_invoice_id.id,
            )
        return vals
