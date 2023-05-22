# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_custom_move_fields(self):
        move_fields = super()._get_custom_move_fields()
        move_fields += [
            "to_refund",
        ]
        return move_fields
