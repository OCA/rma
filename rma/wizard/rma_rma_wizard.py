# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class RmaRmaWizard(models.TransientModel):
    _name = "rma.rma.wizard"
    _description = "Rma Rma Wizard"

    rma_id = fields.Many2one(
        comodel_name="rma",
        default=lambda self: self.env.context.get("active_id", False),
    )
    operation_id = fields.Many2one(
        comodel_name="rma.operation",
        string="Requested operation",
        required=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        rma_id = self.env.context.get("active_id")
        rma = self.env["rma"].browse(rma_id)
        if rma:
            res.update(operation_id=rma.operation_id.id)
        return res

    def _stock_return_picking_vals(self, picking):
        return {
            "picking_id": picking.id,
            "create_rma": True,
            "rma_operation_id": self.operation_id.id,
        }

    def create_rma(self):
        rma = self.rma_id
        delivery_moves = rma.delivery_move_ids.filtered(lambda x: x.state == "done")
        pickings = delivery_moves.picking_id.filtered(lambda x: x.state == "done")
        picking = fields.first(pickings)
        return_wizard = self.env["stock.return.picking"].create(
            self._stock_return_picking_vals(picking)
        )
        # Call the onchange event manually to avoid using Form()
        return_wizard._onchange_create_rma()
        return_wizard.product_return_moves.filtered(
            lambda x: x.move_id not in delivery_moves
        ).unlink()
        res = return_wizard.action_create_returns_all()
        new_picking = self.env[res["res_model"]].browse(res["res_id"])
        new_rma = new_picking.move_ids.rma_receiver_ids
        # Message
        rma_msg = self.env._(
            "This rma has been created from: %(rma_link)s",
            rma_link=rma._get_html_link(),
        )
        new_rma.message_post(body=rma_msg)
        return new_rma

    def create_and_open_rma(self):
        self.ensure_one()
        rma = self.create_rma()
        rma.action_confirm()
        return rma._get_records_action()
