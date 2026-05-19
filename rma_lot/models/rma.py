# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, api, fields, models
from odoo.tools import float_compare


class Rma(models.Model):
    _inherit = "rma"

    domain_lot_id = fields.Binary(compute="_compute_domain_lot_id")
    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Lot/Serial Number",
        domain="domain_lot_id",
        compute="_compute_lot_id",
        store=True,
        readonly=False,
    )
    product_tracking = fields.Selection(related="product_id.tracking")
    lots_visible = fields.Boolean(compute="_compute_lots_visible")

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

    @api.depends("product_id", "product_uom_qty", "warehouse_id")
    def _compute_domain_lot_id(self):
        dp = self.env["decimal.precision"].precision_get("Product Unit of Measure")
        for rec in self:
            domain = []
            if rec.product_id and rec.product_tracking != "none":
                # Only available lots should be displayed. In pickings, the
                # corresponding stock.quant record is selected directly, so we
                # use the same filters that are used.
                quants = self.env["stock.quant"].search(
                    rec._domain_lot_id_quant_domain()
                )
                available_quants = quants.filtered(
                    lambda x, qty=rec.product_uom_qty: float_compare(
                        x.available_quantity,
                        qty,
                        precision_digits=dp,
                    )
                    >= 0
                )
                domain = [("id", "in", available_quants.mapped("lot_id").ids)]
            rec.domain_lot_id = domain

    @api.depends("product_id.tracking")
    def _compute_lots_visible(self):
        for rec in self:
            rec.lots_visible = rec.product_id.tracking != "none"

    def _prepare_delivery_procurement_vals(self, scheduled_date=None):
        vals = super()._prepare_delivery_procurement_vals(scheduled_date=scheduled_date)
        if vals.get("restrict_lot_id") and self.reception_move_id.restrict_lot_id:
            if self.reception_move_id.restrict_lot_id.id != vals.get("restrict_lot_id"):
                vals["move_orig_ids"] = [Command.clear()]  # Avoid inconsistencies
        return vals

    def _prepare_reception_procurement_vals(self, group=None):
        vals = super()._prepare_reception_procurement_vals(group=group)
        vals["restrict_lot_id"] = self.lot_id.id
        return vals

    def _prepare_common_procurement_vals(
        self, warehouse=None, scheduled_date=None, group=None
    ):
        vals = super()._prepare_common_procurement_vals(
            warehouse=warehouse, scheduled_date=scheduled_date, group=group
        )
        replace_lot = self.env.context.get("rma_replace_lot_id")
        if replace_lot:
            vals["restrict_lot_id"] = replace_lot.id
        elif self.operation_id.deliver_same_lot:
            vals["restrict_lot_id"] = self.lot_id.id
        return vals

    @api.depends("move_id", "lot_id")
    def _compute_product_id(self):
        res = super()._compute_product_id()
        for rec in self:
            if not rec.move_id and rec.lot_id:
                self.product_id = rec.lot_id.product_id
        return res

    @api.depends("product_id")
    def _compute_lot_id(self):
        self.update({"lot_id": False})
