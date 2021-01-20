# Copyright 2021 Jarsa
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    repair_id = fields.Many2one(
        related="group_id.repair_id", string="Repair Order", store=True
    )
