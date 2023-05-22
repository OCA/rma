# Copyright 2022 Tecnativa - David Vidal
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
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

    def _prepare_delivery_procurement_group_values(self):
        values = super()._prepare_delivery_procurement_group_values()
        values["carrier_id"] = self._get_default_carrier_id(
            self.company_id, self.partner_shipping_id
        ).id
        return values

    def _prepare_replace_procurement_group_values(self):
        values = super()._prepare_delivery_procurement_group_values()
        values["carrier_id"] = self._get_default_carrier_id(
            self.company_id, self.partner_shipping_id
        ).id
        return values
