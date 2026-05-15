# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class RmaSaleOrderLinkWizard(models.TransientModel):

    _name = "rma.sale.order.link.wizard"
    _description = "Wizard to link existing rma to sale order"

    rma_id = fields.Many2one(comodel_name="rma")
    partner_id = fields.Many2one(related="rma_id.partner_id")
    sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sale Order",
        required=True,
        ondelete="cascade",
        domain="[('partner_id', '=', partner_id), ('state', 'in', ('sale', 'done'))]",
    )

    def action_link_rma_to_sale_order(self):
        self.ensure_one()
        self.rma_id.order_id = self.sale_order_id
        self.rma_id.message_post(
            body=_(
                "Sale Order %(order)s linked manually.", order=self.sale_order_id.name
            )
        )
