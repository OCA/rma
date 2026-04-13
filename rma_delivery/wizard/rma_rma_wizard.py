# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class RmaRmaWizard(models.TransientModel):
    _inherit = "rma.rma.wizard"

    company_id = fields.Many2one(related="rma_id.company_id")
    rma_reception_strategy = fields.Selection(
        related="company_id.rma_reception_strategy"
    )
    partner_shipping_id = fields.Many2one(related="rma_id.partner_shipping_id")
    available_reception_carrier_ids = fields.Many2many(
        comodel_name="delivery.carrier",
        compute="_compute_available_reception_carrier_ids",
    )
    reception_carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Reception Carrier",
        domain="[('id', 'in', available_reception_carrier_ids)]",
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
    def _compute_available_reception_carrier_ids(self):
        carrier_model = self.env["delivery.carrier"]
        for item in self:
            carriers = carrier_model.search(
                carrier_model._check_company_domain(item.company_id)
            )
            item.available_reception_carrier_ids = (
                carriers.available_carriers_rma(item.partner_shipping_id, item)
                if item.partner_shipping_id
                else carriers
            )

    def _stock_return_picking_vals(self, picking):
        vals = super()._stock_return_picking_vals(picking)
        if self.reception_carrier_id:
            vals["reception_carrier_id"] = self.reception_carrier_id.id
        return vals
