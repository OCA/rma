# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class RmaRmaWizard(models.TransientModel):
    _name = "rma.rma.wizard"
    _inherit = ["rma.rma.wizard", "rma.carrier.mixin"]
    _rma_carrier_partner_field = "partner_shipping_id"
    _rma_carrier_source_field = "rma_id"

    company_id = fields.Many2one(related="rma_id.company_id")
    rma_reception_strategy = fields.Selection(
        related="company_id.rma_reception_strategy"
    )
    partner_shipping_id = fields.Many2one(related="rma_id.partner_shipping_id")
    domain_reception_carrier_id = fields.Binary(
        compute="_compute_domain_reception_carrier_id"
    )
    reception_carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        domain="domain_reception_carrier_id",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        rma_id = self.env.context.get("active_id")
        rma = self.env["rma"].browse(rma_id)
        if rma:
            res.update(reception_carrier_id=rma.reception_carrier_id.id)
        return res

    @api.depends("partner_shipping_id")
    def _compute_domain_reception_carrier_id(self):
        for item in self:
            carriers = item._get_rma_available_carriers()
            item.domain_reception_carrier_id = [("id", "in", carriers.ids)]

    def _stock_return_picking_vals(self, picking):
        vals = super()._stock_return_picking_vals(picking)
        if self.reception_carrier_id:
            vals["reception_carrier_id"] = self.reception_carrier_id.id
        return vals
