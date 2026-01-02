# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_new_picking_values(self):
        vals = super()._get_new_picking_values()
        carrier = self.env["delivery.carrier"]
        if self.rma_id:
            carrier = self.rma_id[0]._get_carrier()
        elif self.rma_receiver_ids:
            carrier = self.rma_receiver_ids[0]._get_reception_carrier()
        if carrier and any(rule.propagate_carrier for rule in self.rule_id):
            vals["carrier_id"] = carrier.id
        return vals
