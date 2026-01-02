# Copyright 2022 Tecnativa - David Vidal
# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class Rma(models.Model):
    _inherit = "rma"

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Carrier",
    )
    rma_delivery_strategy = fields.Selection(related="company_id.rma_delivery_strategy")
    reception_carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Reception Carrier",
    )
    rma_reception_strategy = fields.Selection(
        related="company_id.rma_reception_strategy"
    )

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

    def _get_carrier(self):
        self.ensure_one()
        if self.rma_delivery_strategy == "rma_method":
            return self.carrier_id
        else:
            return self._get_default_carrier_id(
                self.company_id, self.partner_shipping_id
            )

    def _get_default_reception_carrier_id(self, company, partner):
        """Gather the company option for default carrier on RMA reception.
        We could either:
          - Get a fixed method
          - Get the partner's defined method (or his commercial entity one)
          - Get the partner's and fallback to a fixed one if defined
        """
        strategy = company.rma_reception_strategy
        delivery_method = company.rma_fixed_reception_strategy
        partner_method = (
            partner.property_delivery_carrier_id
            or partner.commercial_partner_id.property_delivery_carrier_id
        )
        if strategy == "customer_method" or (
            strategy == "mixed_method" and partner_method
        ):
            delivery_method = partner_method
        return delivery_method

    def _get_reception_carrier(self):
        self.ensure_one()
        if self.rma_reception_strategy == "rma_method":
            return self.reception_carrier_id
        else:
            return self._get_default_reception_carrier_id(
                self.company_id, self.partner_shipping_id
            )
