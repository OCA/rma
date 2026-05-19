# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import float_compare


class RmaReDeliveryWizard(models.TransientModel):
    _inherit = "rma.delivery.wizard"

    domain_lot_id = fields.Binary(compute="_compute_domain_lot_id")
    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Lot/Serial Number",
        domain="domain_lot_id",
    )
    product_tracking = fields.Selection(related="product_id.tracking")

    def _domain_lot_id_quant_domain(self):
        """This method defines the domain that will be used to obtain the appropriate
        stock.quant values and is useful for extending to other modules.
        """
        self.ensure_one()
        return [
            ("product_id", "=", self.product_id.id),
            ("quantity", ">=", self.product_uom_qty),
            ("lot_id", "!=", False),
            ("location_id.usage", "=", "internal"),
            ("location_id.warehouse_id", "=", self.warehouse_id.id),
        ]

    @api.depends("product_id", "product_tracking", "product_uom_qty", "warehouse_id")
    def _compute_domain_lot_id(self):
        dp = self.env["decimal.precision"].precision_get("Product Unit of Measure")
        for item in self:
            domain = []
            if item.product_id and item.product_tracking != "none":
                # Only available lots should be displayed. In pickings, the
                # corresponding stock.quant record is selected directly, so we
                # use the same filters that are used.
                quants = self.env["stock.quant"].search(
                    item._domain_lot_id_quant_domain()
                )
                available_quants = quants.filtered(
                    lambda x, qty=item.product_uom_qty: float_compare(
                        x.available_quantity,
                        qty,
                        precision_digits=dp,
                    )
                    >= 0
                )
                domain = [("id", "in", available_quants.mapped("lot_id").ids)]
            item.domain_lot_id = domain

    @api.onchange("product_id")
    def _onchange_product_id(self):
        res = super()._onchange_product_id()
        if self.product_id and self.product_tracking:
            rma_ids = self.env.context.get("active_ids")
            rma = self.env["rma"].browse(rma_ids)
            if len(rma) == 1:
                if rma.lot_id.product_id == self.product_id:
                    self.lot_id = rma.lot_id
                else:
                    self.lot_id = False
        return res

    def action_deliver(self):
        if self.type == "replace" and self.lot_id:
            self = self.with_context(rma_replace_lot_id=self.lot_id)
        return super().action_deliver()
