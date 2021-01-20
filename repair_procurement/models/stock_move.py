# Copyright 2021 Jarsa
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    repair_line_id = fields.Many2one("repair.line", index=True)
