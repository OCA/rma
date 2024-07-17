# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrderRmaWizard(models.TransientModel):

    _inherit = "sale.order.rma.wizard"

    reason_id = fields.Many2one(comodel_name="rma.reason")
