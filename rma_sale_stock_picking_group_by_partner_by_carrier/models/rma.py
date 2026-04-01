# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, models


class Rma(models.Model):
    _inherit = "rma"

    def _prepare_procurement_group_vals(self):
        # Bridge sale_id (M2O) → sale_ids (M2M) on the procurement group.
        # stock_picking_group_by_partner_by_carrier computes
        # stock.picking.sale_ids from move_ids.group_id.sale_ids (M2M),
        # but rma_sale only sets sale_id (M2O). Without this bridge,
        # RMA return pickings are invisible from the SO "Deliveries" button.
        vals = super()._prepare_procurement_group_vals()
        sale_id = vals.get("sale_id")
        sale_ids = vals.get("sale_ids")
        if sale_id:
            if sale_ids:
                sale_ids.append(Command.link(sale_id))
            else:
                vals["sale_ids"] = [Command.link(sale_id)]
        return vals
