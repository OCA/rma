# Copyright 2024 Raumschmiede GmbH
# Copyright 2024 BCIM
# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrderLineRmaWizard(models.TransientModel):

    _inherit = "sale.order.line.rma.wizard"

    reason_id = fields.Many2one(
        comodel_name="rma.reason",
        compute="_compute_reason_id",
        store=True,
        readonly=False,
    )
    is_rma_reason_required = fields.Boolean(
        related="order_id.company_id.is_rma_reason_required"
    )

    @api.depends("wizard_id.reason_id")
    def _compute_reason_id(self):
        for rec in self:
            if rec.wizard_id.reason_id:
                rec.reason_id = rec.wizard_id.reason_id

    def _prepare_rma_values(self):
        values = super()._prepare_rma_values()
        if self.reason_id:
            values["reason_id"] = self.reason_id.id
        return values
