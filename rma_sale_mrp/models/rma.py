# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import UserError


class Rma(models.Model):
    _inherit = "rma"

    phantom_bom_product = fields.Many2one(
        comodel_name="product.product",
        string="Related kit product",
        readonly=True,
    )
    kit_qty = fields.Float(
        string="Kit quantity",
        digits="Product Unit of Measure",
        readonly=True,
        help="To how many kits this components corresponds to. Used mainly "
        "for refunding the right quantity",
    )
    rma_kit_register = fields.Char(readonly=True)

    def _get_refund_line_quantity(self):
        """Refund the kit, not the component"""
        if self.phantom_bom_product:
            uom = self.sale_line_id.product_uom or self.phantom_bom_product.uom_id
            return (self.kit_qty, uom)
        return (self.product_uom_qty, self.product_uom)

    def action_refund(self):
        """We want to process them altogether"""
        phantom_rmas = self.filtered("phantom_bom_product")
        phantom_rmas |= self.search(
            [
                ("rma_kit_register", "in", phantom_rmas.mapped("rma_kit_register")),
                ("id", "not in", phantom_rmas.ids),
            ]
        )
        self -= phantom_rmas
        for rma_kit_register in phantom_rmas.mapped("rma_kit_register"):
            # We want to avoid refunding kits that aren't completely processed
            rmas_by_register = phantom_rmas.filtered(
                lambda x: x.rma_kit_register == rma_kit_register
            )
            if any(rmas_by_register.filtered(lambda x: x.state != "received")):
                raise UserError(
                    _("You can't refund a kit in wich some RMAs aren't received")
                )
            self |= rmas_by_register[0]
        res = super().action_refund()
        # We can just link the line to an RMA but we can link several RMAs
        # to one invoice line.
        for rma_kit_register in set(phantom_rmas.mapped("rma_kit_register")):
            grouped_rmas = phantom_rmas.filtered(
                lambda x: x.rma_kit_register == rma_kit_register
            )
            lead_rma = grouped_rmas.filtered("refund_line_id")
            grouped_rmas -= lead_rma
            grouped_rmas.write(
                {
                    "refund_line_id": lead_rma.refund_line_id.id,
                    "refund_id": lead_rma.refund_id.id,
                    "state": "refunded",
                }
            )
        return res

    def action_draft(self):
        if self.filtered(lambda r: r.state == "cancelled" and r.phantom_bom_product):
            raise UserError(
                _(
                    "To avoid kit quantities inconsistencies it is not possible to convert "
                    "to draft a cancelled RMA. You should do a new one from the sales order."
                )
            )
        return super().action_draft()
