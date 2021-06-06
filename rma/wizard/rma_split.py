# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class RmaReSplitWizard(models.TransientModel):
    _name = "rma.split.wizard"
    _description = "RMA Split Wizard"

    rma_id = fields.Many2one(
        comodel_name="rma",
        string="RMA",
    )
    product_uom_qty = fields.Float(
        string="Quantity to extract",
        digits="Product Unit of Measure",
        required=True,
        help="Quantity to extract to a new RMA.",
    )
    product_uom = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of measure",
        required=True,
    )

    _sql_constraints = [
        (
            "check_product_uom_qty_positive",
            "CHECK(product_uom_qty > 0)",
            "Quantity must be greater than 0.",
        ),
    ]

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields, attributes=attributes)
        rma_id = self.env.context.get("active_id")
        rma = self.env["rma"].browse(rma_id)
        res["product_uom"]["domain"] = [
            ("category_id", "=", rma.product_uom.category_id.id)
        ]
        return res

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        rma_id = self.env.context.get("active_id")
        rma = self.env["rma"].browse(rma_id)
        res.update(
            rma_id=rma.id,
            product_uom_qty=rma.remaining_qty,
            product_uom=rma.product_uom.id,
        )
        return res

    def action_split(self):
        self.ensure_one()
        extracted_rma = self.rma_id.extract_quantity(
            self.product_uom_qty, self.product_uom
        )
        return {
            "name": _("Extracted RMA"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "rma",
            "views": [(self.env.ref("rma.rma_view_form").id, "form")],
            "res_id": extracted_rma.id,
        }
