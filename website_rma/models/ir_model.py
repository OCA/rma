# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class IrModel(models.Model):
    _inherit = "ir.model"

    @api.model
    def get_authorized_fields(self, model_name):
        """Hack this method to force some rma fields to be authorized in
        creating an object from a web form using the website_form module.

        Those fields are readonly in all states except 'draft' state,
        but the main method get_authorized_fields interprets them as
        readonly always.
        """
        res = super().get_authorized_fields(model_name)
        if model_name == "rma":
            auth_fields = ["product_uom_qty", "product_uom", "partner_id"]
            res.update(self.env[model_name].fields_get(auth_fields))
        return res
