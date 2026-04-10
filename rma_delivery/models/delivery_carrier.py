# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    # TODO 19.0: The available_carriers_* methods should be removed, and the core
    # methods should be reused and extended for RMA.
    def available_carriers_picking(self, partner, picking):
        return self.filtered(lambda c: c._match_picking(partner, picking))

    def available_carriers_rma(self, partner, rma):
        return self.filtered(lambda c: c._match_rma(partner, rma))

    def _match_picking(self, partner, picking):
        self.ensure_one()
        return (
            self._match_address(partner)
            and self._match_must_have_tags_picking(picking)
            and self._match_excluded_tags_picking(picking)
            and self._match_weight_picking(picking)
            and self._match_volume_picking(picking)
        )

    def _match_rma(self, partner, rma):
        self.ensure_one()
        return (
            self._match_address(partner)
            and self._match_must_have_tags_rma(rma)
            and self._match_excluded_tags_rma(rma)
            and self._match_weight_rma(rma)
            and self._match_volume_rma(rma)
        )

    def _match_must_have_tags_picking(self, picking):
        self.ensure_one()
        return not self.must_have_tag_ids or any(
            tag in picking.move_ids.product_id.all_product_tag_ids
            for tag in self.must_have_tag_ids
        )

    def _match_must_have_tags_rma(self, rma):
        self.ensure_one()
        return not self.must_have_tag_ids or any(
            tag in rma.product_id.all_product_tag_ids for tag in self.must_have_tag_ids
        )

    def _match_excluded_tags_picking(self, picking):
        self.ensure_one()
        return not any(
            tag in picking.move_ids.product_id.all_product_tag_ids
            for tag in self.excluded_tag_ids
        )

    def _match_excluded_tags_rma(self, rma):
        self.ensure_one()
        return not any(
            tag in rma.product_id.all_product_tag_ids for tag in self.excluded_tag_ids
        )

    def _match_weight_picking(self, picking):
        self.ensure_one()
        return (
            not self.max_weight
            or sum(
                move.product_id.weight * move.product_uom_qty
                for move in picking.move_ids
            )
            <= self.max_weight
        )

    def _match_weight_rma(self, rma):
        self.ensure_one()
        return (
            not self.max_weight
            or (rma.product_id.weight * rma.product_uom_qty) <= self.max_weight
        )

    def _match_volume_picking(self, picking):
        self.ensure_one()
        return (
            not self.max_volume
            or sum(
                move.product_id.volume * move.product_uom_qty
                for move in picking.move_ids
            )
            <= self.max_volume
        )

    def _match_volume_rma(self, rma):
        self.ensure_one()
        return (
            not self.max_volume
            or (rma.product_id.volume * rma.product_uom_qty) <= self.max_volume
        )
