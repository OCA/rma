# Copyright 2022 Tecnativa - David Vidal
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class Rma(models.Model):
    _inherit = "rma"

    def _get_default_carrier_id(self, company, partner):
        """Gather the company option for default carrier on RMA returns. We could
        either:
          - Get a fixed method
          - Get the partner's defined method (or his commercial entity one)
          - Get the partner's and fallback to a fixed one if defined
        """
        strategy = company.rma_delivery_strategy
        delivery_method = company.rma_fixed_delivery_method
        partner_method = (
            partner.property_delivery_carrier_id
            or partner.commercial_partner_id.property_delivery_carrier_id
        )
        if strategy == "customer_method" or (
            strategy == "mixed_method" and partner_method
        ):
            delivery_method = partner_method
        return delivery_method

    def create_replace(self, scheduled_date, warehouse, product, qty, uom):
        existing_pickings = self.delivery_move_ids.mapped("picking_id")
        res = super().create_replace(scheduled_date, warehouse, product, qty, uom)
        new_pickings = self.delivery_move_ids.mapped("picking_id") - existing_pickings
        for picking in new_pickings:
            picking.carrier_id = self._get_default_carrier_id(
                picking.company_id, picking.partner_id
            )
        return res

    def create_return(self, scheduled_date, qty=None, uom=None):
        existing_pickings = self.delivery_move_ids.mapped("picking_id")
        res = super().create_return(scheduled_date, qty, uom)
        new_pickings = self.delivery_move_ids.mapped("picking_id") - existing_pickings
        for picking in new_pickings:
            picking.carrier_id = self._get_default_carrier_id(
                picking.company_id, picking.partner_id
            )
        return res
