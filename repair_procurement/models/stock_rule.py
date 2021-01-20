# Copyright 2021 Jarsa
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_custom_move_fields(self):
        fields = super()._get_custom_move_fields()
        fields += ["repair_line_id"]
        return fields
