# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class RmaCarrierMixin(models.AbstractModel):
    _name = "rma.carrier.mixin"
    _description = "Mixin to use RMA Carrier"
    _rma_carrier_partner_field = "partner_id"
    _rma_carrier_source_field = "rma_id"

    def _get_rma_available_carriers(self):
        """This method will be used to obtain the available carriers based on the
        defined partner and RMA fields.
        """
        self.ensure_one()
        carrier_model = self.env["delivery.carrier"]
        carriers = carrier_model.search(
            carrier_model._check_company_domain(self.company_id)
        )
        partner_field = self[self._rma_carrier_partner_field]
        source_f_name = self._rma_carrier_source_field
        source_field = self[source_f_name] if source_f_name else self
        available_carriers = (
            carriers.available_carriers(partner_field, source_field)
            if partner_field
            else carriers
        )
        return available_carriers
