# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class Rma(models.Model):

    _inherit = "rma"

    def _prepare_procurement_group_vals(self):
        vals = super()._prepare_procurement_group_vals()
        carrier = self._get_default_carrier_id(self.company_id, self.partner_id)
        if carrier:
            vals["carrier_id"] = carrier.id
        return vals
