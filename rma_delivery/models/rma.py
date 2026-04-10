# Copyright 2022 Tecnativa - David Vidal
# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class Rma(models.Model):
    _inherit = "rma"

    available_carrier_ids = fields.Many2many(
        comodel_name="delivery.carrier",
        compute="_compute_available_carrier_ids",
    )
    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Carrier",
        domain="[('id', 'in', available_carrier_ids)]",
    )
    rma_delivery_strategy = fields.Selection(related="company_id.rma_delivery_strategy")
    reception_carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Reception Carrier",
        domain="[('id', 'in', available_carrier_ids)]",
    )
    rma_reception_strategy = fields.Selection(
        related="company_id.rma_reception_strategy"
    )

    @api.depends("partner_shipping_id", "product_id", "product_uom_qty")
    def _compute_available_carrier_ids(self):
        carrier_model = self.env["delivery.carrier"]
        for item in self:
            carriers = carrier_model.search(
                carrier_model._check_company_domain(item.company_id)
            )
            item.available_carrier_ids = (
                carriers.available_carriers_rma(item.partner_shipping_id, item)
                if item.partner_shipping_id
                else carriers
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

    def action_open_choose_carrier_wizard(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "rma_delivery.rma_choose_delivery_carrier_action"
        )
        # Force active_id to avoid issues when coming from smart buttons
        # in other models
        action["context"] = dict(self.env.context)
        action["context"].update(
            active_model=self._name, active_id=self.id, active_ids=self.ids
        )
        return action
