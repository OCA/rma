# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_rma_wizard_line_vals(self, data):
        """Set the real kit product"""
        vals = super()._prepare_rma_wizard_line_vals(data)
        if data.get("phantom_bom_product"):
            vals["phantom_bom_product"] = data.get("phantom_bom_product").id
            vals["per_kit_quantity"] = data.get("per_kit_quantity", 0)
        vals["phantom_kit_line"] = data.get("phantom_kit_line", False)
        return vals

    def get_delivery_rma_data(self):
        """Get the phantom lines we'll be showing in the wizard"""
        data_list = super().get_delivery_rma_data()
        kit_products = {
            (x.get("phantom_bom_product"), x.get("sale_line_id"))
            for x in data_list
            if x.get("phantom_bom_product")
        }
        # For every unique phantom product we'll create a phantom line wich
        # will be using as the control in frontend and for display purposes
        # in backend
        for product, sale_line_id in kit_products:
            order_line_obj = self.env["sale.order.line"]
            product_obj = self.env["product.product"]
            first_component_dict = next(
                x
                for x in data_list
                if x.get("phantom_bom_product", product_obj) == product
                and x.get("sale_line_id", order_line_obj) == sale_line_id
            )
            component_index = data_list.index(first_component_dict)
            # Prevent miscalculation if there partial deliveries
            quantity = sum(
                x.get("quantity", 0)
                for x in data_list
                if x.get("sale_line_id")
                and x.get("product") == first_component_dict.get("product")
                and x.get("sale_line_id") == first_component_dict.get("sale_line_id")
            )
            data_list.insert(
                component_index,
                {
                    "product": product,
                    "quantity": (
                        first_component_dict.get("per_kit_quantity")
                        and (quantity / first_component_dict.get("per_kit_quantity"))
                    ),
                    "uom": first_component_dict.get(
                        "sale_line_id", order_line_obj
                    ).product_uom,
                    "phantom_kit_line": True,
                    "picking": False,
                    "sale_line_id": first_component_dict.get(
                        "sale_line_id", order_line_obj
                    ),
                },
            )
        return data_list


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def get_delivery_move(self):
        self.ensure_one()
        if self.product_id and not self._rma_is_kit_product():
            return super().get_delivery_move()
        return self.move_ids.filtered(
            lambda m: (
                m.state == "done"
                and not m.scrapped
                and m.location_dest_id.usage == "customer"
                and (
                    not m.origin_returned_move_id
                    or (m.origin_returned_move_id and m.to_refund)
                )
            )
        )

    def prepare_sale_rma_data(self):
        """We'll take both the sale order product and the phantom one so we
        can play with them when filtering or showing to the customer"""
        self.ensure_one()
        data = super().prepare_sale_rma_data()
        if self.product_id and self._rma_is_kit_product():
            for d in data:
                d.update(
                    {
                        "phantom_bom_product": self.product_id,
                        "per_kit_quantity": self._get_kit_qty(d.get("product")),
                    }
                )
        return data

    def _get_kit_qty(self, product_id):
        """Compute how many kit components were demanded from this line. We
        rely on the matching of sale order and pickings demands, but if those
        were manually changed, it could lead to inconsistencies"""
        self.ensure_one()
        if (
            self.product_id
            and not self._rma_is_kit_product()
            or not self.product_uom_qty
        ):
            return 0
        component_demand = sum(
            self.move_ids.filtered(
                lambda x: x.product_id == product_id and not x.origin_returned_move_id
            ).mapped("product_uom_qty")
        )
        return component_demand / self.product_uom_qty

    def _rma_is_kit_product(self):
        """The method _is_phantom_bom isn't available anymore. We wan't to use
        the same rule Odoo does in core"""
        bom = (
            self.env["mrp.bom"]
            .sudo()
            ._bom_find(
                products=self.product_id,
                company_id=self.company_id.id,
                bom_type="phantom",
            )
        )
        return bom and bom.get(self.product_id).type == "phantom"
