# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, _, api, fields, models
from odoo.exceptions import ValidationError


class Rma(models.Model):
    _name = "rma"
    _inherit = ["rma", "restocking.fee.mixin"]

    restocking_fee_invoice_id = fields.Many2one(
        comodel_name="account.move", readonly=True
    )
    manual_restocking_fee_invoice_needed = fields.Boolean(
        compute="_compute_manual_restocking_fee_invoice_needed"
    )
    restocking_fee_type = fields.Selection(
        compute="_compute_restocking_fee", store=True, readonly=False
    )
    restocking_fee_amount = fields.Float(
        compute="_compute_restocking_fee", store=True, readonly=False
    )
    restocking_fee_visibility = fields.Boolean(
        compute="_compute_restocking_fee_visibility"
    )

    @api.depends("operation_id")
    def _compute_restocking_fee(self):
        for rec in self:
            rec.update(
                {
                    "restocking_fee_type": rec.operation_id.restocking_fee_type,
                    "restocking_fee_amount": rec.operation_id.restocking_fee_amount,
                }
            )

    @api.depends("operation_id")
    def _compute_restocking_fee_visibility(self):
        for rec in self:
            rec.restocking_fee_visibility = bool(rec.action_create_receipt)

    @api.depends(
        "operation_id.action_create_receipt",
        "operation_id.action_create_refund",
        "restocking_fee_type",
        "restocking_fee_invoice_id",
    )
    def _compute_manual_restocking_fee_invoice_needed(self):
        for rec in self:
            rec.manual_restocking_fee_invoice_needed = (
                not rec.restocking_fee_invoice_id
                and rec.operation_id.action_create_receipt
                and rec.operation_id.action_create_refund != "update_quantity"
                and rec.restocking_fee_type
            )

    def _prepare_reception_procurement_vals(self, group=None):
        vals = super()._prepare_reception_procurement_vals(group=group)
        vals["charge_restocking_fee"] = bool(self.restocking_fee_type)
        return vals

    def _create_restocking_fee_invoice(self):
        for rec in self:
            if not rec.manual_restocking_fee_invoice_needed:
                continue
            rec.restocking_fee_invoice_id = self.env["account.move"].create(
                rec._prepare_restocking_fee_invoice_vals()
            )

    def _prepare_restocking_fee_invoice_vals(self):
        self.ensure_one()
        return {
            "move_type": "out_invoice",
            "company_id": self.company_id.id,
            "partner_id": self.partner_invoice_id.id,
            "invoice_line_ids": [
                Command.create(self._prepare_restocking_fee_invoice_line_vals())
            ],
        }

    def _get_restocking_fee_invoice_line_name(self):
        lang = self.partner_id.lang
        return _(
            "Restocking fee for %(prod_uom_qty)s %(prod_uom)s. RMA %(rma)s",
            prod_uom_qty=self.product_uom_qty,
            prod_uom=self.product_uom.with_context(lang=lang).name,
            rma=self.name,
        )

    def _prepare_restocking_fee_invoice_line_vals(self):
        self.ensure_one()
        product_id = self.company_id.restocking_fee_product_id
        if not product_id:
            raise ValidationError(
                _(
                    "No product configured for restocking fee. "
                    "Please fix the configuration into stock settings or "
                    "contact you administrator."
                )
            )
        name = self.with_context(
            lang=self.partner_id.lang
        )._get_restocking_fee_invoice_line_name()
        return {
            "name": name,
            "quantity": 1,
            "product_uom_id": product_id.uom_id.id,
            "product_id": product_id.id,
            "price_unit": self._get_restocking_fee_amount(),
        }

    def action_view_restocking_fee_invoice(self):
        self.ensure_one()
        return {
            "name": self.env._("Invoice"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "account.move",
            "views": [(self.env.ref("account.view_move_form").id, "form")],
            "res_id": self.restocking_fee_invoice_id.id,
        }

    def _get_restocking_fee_amount(self):
        self.ensure_one()
        if not self.restocking_fee_type:
            return 0
        if self.restocking_fee_type == "fixed":
            return self.restocking_fee_amount
        if self.sale_line_id:
            price_unit = self.sale_line_id.price_unit
            price_unit = self.sale_line_id.product_uom._compute_price(
                price_unit, self.product_uom
            )
        else:
            price_unit = self.product_id.lst_price
        return (price_unit * (self.restocking_fee_amount / 100)) * self.product_uom_qty
