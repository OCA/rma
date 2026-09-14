# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def _match_must_have_tags(self, source):
        self.ensure_one()
        if source._name == "rma":
            products = source.product_id
            return not self.must_have_tag_ids or any(
                tag in products.all_product_tag_ids for tag in self.must_have_tag_ids
            )
        return super()._match_must_have_tags(source)

    def _match_excluded_tags(self, source):
        self.ensure_one()
        if source._name == "rma":
            products = source.product_id
            return not any(
                tag in products.all_product_tag_ids for tag in self.excluded_tag_ids
            )
        return super()._match_excluded_tags(source)

    def _match_weight(self, source):
        self.ensure_one()
        if source._name == "rma":
            total_weight = source.product_id.weight * source.product_uom_qty
            return not self.max_weight or total_weight <= self.max_weight
        return super()._match_weight(source)

    def _match_volume(self, source):
        self.ensure_one()
        if source._name == "rma":
            total_volume = source.product_id.volume * source.product_uom_qty
            return not self.max_volume or total_volume <= self.max_volume
        return super()._match_volume(source)
