# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class RmaChooseDeliveryCarrier(models.TransientModel):
    _name = "rma.choose.delivery.carrier"
    _description = "RMA Delivery Carrier Selection Wizard"

    rma_id = fields.Many2one(
        comodel_name="rma",
        default=lambda self: self.env.context.get("active_id", False),
    )
    carrier_type = fields.Selection(
        [
            ("reception", "Reception"),
            ("delivery", "Delivery"),
        ],
        default="reception",
        readonly=True,
    )
    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier", string="Carrier", required=True
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        rma_id = self.env.context.get("active_id")
        rma = self.env["rma"].browse(rma_id)
        if rma:
            carrier_type = "reception" if rma.state == "confirmed" else "delivery"
            carrier = (
                rma.reception_carrier_id
                if carrier_type == "reception"
                else rma.carrier_id
            )
            res.update(carrier_type=carrier_type, carrier_id=carrier.id)
        return res

    def _get_pending_moves(self):
        rma = self.rma_id
        moves = (
            rma.reception_move_id
            if self.carrier_type == "reception"
            else rma.delivery_move_ids
        )
        return moves.filtered(lambda x: x.state not in ("done", "cancel"))

    def _prepare_picking_vals(self):
        return {"carrier_id": self.carrier_id.id}

    def _prepare_rma_vals(self):
        f_name = (
            "reception_carrier_id" if self.carrier_type == "reception" else "carrier_id"
        )
        return {f_name: self.carrier_id.id}

    def button_confirm(self):
        moves = self._get_pending_moves()
        moves.picking_id.write(self._prepare_picking_vals())
        self.rma_id.write(self._prepare_rma_vals())
