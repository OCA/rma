# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SaleOrderRmaWizard(models.TransientModel):
    _inherit = "sale.order.rma.wizard"

    # We wan't to separate components from the main line so we can separate
    # them and hide them in the wizard
    component_line_ids = fields.One2many(
        comodel_name="sale.order.line.rma.wizard.component",
        inverse_name="wizard_id",
        string="Component Lines",
    )

    @api.model
    def create(self, vals):
        """Split component lines"""
        if "line_ids" in vals and vals.get("line_ids"):
            line_ids = [
                (x[0], x[1], x[2]) for x in vals.get("line_ids")
                if not x[2].get("phantom_bom_product")
            ]
            component_line_ids = [
                (x[0], x[1], x[2]) for x in vals.get("line_ids")
                if x[2].get("phantom_bom_product")
            ]
            vals.update({
                "line_ids": line_ids,
                "component_line_ids": component_line_ids,
            })
        return super().create(vals)

    def create_rma(self, from_portal=None):
        """We'll decompose the RMAs and remove the phantom lines"""
        phantom_lines = self.line_ids.filtered("phantom_kit_line")
        # Coming from the portal, we'll compute how many per kit to receive.
        # From backend we'll be returning them from each individual component
        # import pdb; pdb.set_trace()
        for line in phantom_lines:
            kit_lines = self.component_line_ids.filtered(
                lambda x: x.phantom_bom_product == line.product_id
                and x.sale_line_id == line.sale_line_id
            )
            component_products = kit_lines.mapped("product_id")
            for product in component_products:
                product_kit_lines = kit_lines.filtered(
                    lambda x: x.product_id == product)
                qty_to_return = product_kit_lines[0].per_kit_quantity * line.quantity
                while qty_to_return:
                    for kit_line in product_kit_lines:
                        kit_line.quantity = min(qty_to_return, kit_line.quantity)
                        kit_line.operation_id = line.operation_id
                        kit_line.kit_qty_done = (
                            kit_line.quantity / kit_line.per_kit_quantity)
                        qty_to_return -= kit_line.quantity
            # Finally we add them the main line_ids
            kit_line_vals = [
                (0, 0, x._convert_to_write(x._cache)) for x in kit_lines]
            self.update({"line_ids": kit_line_vals})
        # We don't need them anymore
        phantom_lines.unlink()
        return super().create_rma(from_portal=from_portal)


class SaleOrderLineRmaWizard(models.TransientModel):
    _inherit = "sale.order.line.rma.wizard"

    phantom_bom_product = fields.Many2one(
        comodel_name="product.product",
    )
    kit_qty_done = fields.Float(
        readonly=True,
        help="Used to inform kit qty used in the rma. Will be useful to refund",
    )
    per_kit_quantity = fields.Float(
        readonly=True,
    )
    phantom_kit_line = fields.Boolean(readonly=True)

    @api.depends("picking_id")
    def _compute_move_id(self):
        """We need to process kit components separately so we can match them
        against their phantom product"""
        not_kit = self.filtered(
            lambda x: not x.phantom_bom_product and
            not x.product_id._is_phantom_bom())
        super(SaleOrderLineRmaWizard, not_kit)._compute_move_id()
        for line in self.filtered(
                lambda x: x.phantom_bom_product and x.picking_id):
            line.move_id = line.picking_id.move_lines.filtered(
                lambda ml: (
                    ml.product_id == line.product_id
                    and ml.sale_line_id == line.sale_line_id
                    and ml.sale_line_id.product_id == line.phantom_bom_product
                    and ml.sale_line_id.order_id == line.order_id))

    def _prepare_rma_values(self):
        """It will be used as a reference for the components"""
        res = super()._prepare_rma_values()
        if self.phantom_bom_product:
            unique_register = "{}-{}-{}".format(
                self.wizard_id.id,
                self.phantom_bom_product.id,
                self.sale_line_id.id
            )
            res.update({
                "phantom_bom_product": self.phantom_bom_product.id,
                "kit_qty": self.kit_qty_done,
                "rma_kit_register": unique_register,
            })
        return res


class SaleOrderLineRmaWizardComponent(models.TransientModel):
    _name = "sale.order.line.rma.wizard.component"
    _inherit = "sale.order.line.rma.wizard"
    _description = "Used to hide kit components in the wizards"
