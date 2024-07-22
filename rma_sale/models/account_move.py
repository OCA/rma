# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def button_cancel(self):
        """If this a refund linked to an RMA, undo the linking of the reception move for
        having proper quantities and status.
        """
        for rma in self.env["rma"].sudo().search([("refund_id", "in", self.ids)]):
            if rma.sale_line_id:
                rma._unlink_refund_with_reception_move()
        return super().button_cancel()

    def button_draft(self):
        """Relink the reception move when passing the refund again to draft."""
        for rma in self.env["rma"].sudo().search([("refund_id", "in", self.ids)]):
            if rma.sale_line_id:
                rma._link_refund_with_reception_move()
        return super().button_draft()

    def unlink(self):
        """If the invoice is removed, rollback the quantities correction"""
        for rma in self.invoice_line_ids.rma_id.filtered("sale_line_id"):
            rma._unlink_refund_with_reception_move()
        return super().unlink()
