# Copyright 2020 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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
                (x[0], x[1], x[2])
                for x in vals.get("line_ids")
                if not x[2].get("phantom_bom_product")
            ]
            component_line_ids = [
                (x[0], x[1], x[2])
                for x in vals.get("line_ids")
                if x[2].get("phantom_bom_product")
            ]
            vals.update(
                {"line_ids": line_ids, "component_line_ids": component_line_ids}
            )
        return super().create(vals)

    def create_rma(self, from_portal=None):
        """We kept the component lines in the shade and now we need to take
        the ones linked to the phatom lines (kits) to create the proper RMA
        for each component according to the proper component quantities"""
        phantom_lines = self.line_ids.filtered("phantom_kit_line")
        kit_line_vals = []
        for line in phantom_lines:
            # There could be two lines for the same product, so we need to
            # split them to get the right quantities and operations for each
            # one and then group them by product to process them altogether
            kit_component_lines = self.component_line_ids.filtered(
                lambda x: x.phantom_bom_product == line.product_id
                and x.sale_line_id == line.sale_line_id
            )
            for product in kit_component_lines.mapped("product_id"):
                product_kit_component_lines = kit_component_lines.filtered(
                    lambda x: x.product_id == product and x.quantity
                )
                if not product_kit_component_lines:
                    raise ValidationError(
                        _(
                            "The kit corresponding to the product %s can't be "
                            "put in the RMA. Either all or some of the components "
                            "where already put in another RMA"
                        )
                        % line.product_id.name
                    )
                qty_to_return = (
                    product_kit_component_lines[0].per_kit_quantity * line.quantity
                )
                while qty_to_return > 0:
                    for kit_line in product_kit_component_lines:
                        kit_line.quantity = min(qty_to_return, kit_line.quantity)
                        kit_line.operation_id = line.operation_id
                        kit_line.description = line.description
                        kit_line.kit_qty_done = (
                            kit_line.quantity / kit_line.per_kit_quantity
                        )
                        qty_to_return -= kit_line.quantity
            kit_line_vals += [
                (0, 0, x._convert_to_write(x._cache)) for x in kit_component_lines
            ]
        self.update({"line_ids": kit_line_vals})
        # We don't need the phantom lines anymore as we already have the
        # kit component ones.
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
            lambda x: not x.phantom_bom_product
            and not x.sale_line_id._rma_is_kit_product()
        )
        res = super(SaleOrderLineRmaWizard, not_kit)._compute_move_id()
        for line in self.filtered(lambda x: x.phantom_bom_product and x.picking_id):
            line.move_id = line.picking_id.move_ids.filtered(
                lambda ml: (
                    ml.product_id == line.product_id
                    and ml.sale_line_id == line.sale_line_id
                    and ml.sale_line_id.product_id == line.phantom_bom_product
                    and ml.sale_line_id.order_id == line.order_id
                )
            )
        return res

    def _prepare_rma_values(self):
        """It will be used as a reference for the components"""
        res = super()._prepare_rma_values()
        if self.phantom_bom_product:
            unique_register = "{}-{}-{}".format(
                self.wizard_id.id, self.phantom_bom_product.id, self.sale_line_id.id
            )
            res.update(
                {
                    "phantom_bom_product": self.phantom_bom_product.id,
                    "kit_qty": self.kit_qty_done,
                    "rma_kit_register": unique_register,
                }
            )
        return res


class SaleOrderLineRmaWizardComponent(models.TransientModel):
    _name = "sale.order.line.rma.wizard.component"
    _inherit = "sale.order.line.rma.wizard"
    _description = "Used to hide kit components in the wizards"
