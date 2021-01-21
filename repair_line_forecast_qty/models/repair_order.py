# Copyright 2021 Jarsa
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class RepairOrder(models.Model):
    _inherit = "repair.line"

    product_type = fields.Selection(related="product_id.type")
    virtual_available_at_date = fields.Float(
        compute="_compute_qty_at_date", digits="Product Unit of Measure"
    )
    scheduled_date = fields.Datetime(compute="_compute_qty_at_date")
    forecast_expected_date = fields.Datetime(compute="_compute_qty_at_date")
    free_qty_today = fields.Float(
        compute="_compute_qty_at_date", digits="Product Unit of Measure"
    )
    qty_available_today = fields.Float(compute="_compute_qty_at_date")
    qty_to_deliver = fields.Float(
        compute="_compute_qty_to_deliver", digits="Product Unit of Measure"
    )
    display_qty_widget = fields.Boolean(compute="_compute_qty_to_deliver")
    is_mto = fields.Boolean(compute="_compute_is_mto")
    warehouse_id = fields.Many2one(
        "stock.warehouse", compute="_compute_qty_at_date", store=True
    )

    @api.depends("product_type", "product_uom_qty", "repair_id.state", "product_uom")
    def _compute_qty_to_deliver(self):
        """Compute the visibility of the inventory widget."""
        for line in self:
            line.qty_to_deliver = line.product_uom_qty
            if (
                line.repair_id.state == "draft"
                and line.product_type == "product"
                and line.product_uom
                and line.qty_to_deliver > 0
            ):
                line.display_qty_widget = True
            else:
                line.display_qty_widget = False

    @api.depends("product_id", "product_uom_qty", "product_uom", "location_id")
    def _compute_qty_at_date(self):
        treated = self.browse()
        qty_processed_per_product = defaultdict(lambda: 0)
        grouped_lines = defaultdict(lambda: self.env["repair.line"])
        for line in self.filtered(lambda l: l.state == "draft"):
            if not (line.product_id and line.display_qty_widget):
                continue
            warehouse = self.location_id.get_warehouse()
            line.warehouse_id = warehouse
            grouped_lines[(warehouse.id, fields.Date.context_today(self))] |= line

        for (warehouse, scheduled_date), lines in grouped_lines.items():
            product_qties = (
                lines.mapped("product_id")
                .with_context(warehouse=warehouse)
                .read(
                    [
                        "qty_available",
                        "free_qty",
                        "virtual_available",
                    ]
                )
            )
            qties_per_product = {
                product["id"]: (
                    product["qty_available"],
                    product["free_qty"],
                    product["virtual_available"],
                )
                for product in product_qties
            }
            for line in lines:
                line.scheduled_date = scheduled_date
                (
                    qty_available_today,
                    free_qty_today,
                    virtual_available_at_date,
                ) = qties_per_product[line.product_id.id]
                line.qty_available_today = (
                    qty_available_today - qty_processed_per_product[line.product_id.id]
                )
                line.free_qty_today = (
                    free_qty_today - qty_processed_per_product[line.product_id.id]
                )
                line.virtual_available_at_date = (
                    virtual_available_at_date
                    - qty_processed_per_product[line.product_id.id]
                )
                line.forecast_expected_date = scheduled_date
                product_qty = line.product_uom_qty
                if (
                    line.product_uom
                    and line.product_id.uom_id
                    and line.product_uom != line.product_id.uom_id
                ):
                    line.qty_available_today = line.product_id.uom_id._compute_quantity(
                        line.qty_available_today, line.product_uom
                    )
                    line.free_qty_today = line.product_id.uom_id._compute_quantity(
                        line.free_qty_today, line.product_uom
                    )
                    line.virtual_available_at_date = (
                        line.product_id.uom_id._compute_quantity(
                            line.virtual_available_at_date, line.product_uom
                        )
                    )
                    product_qty = line.product_uom._compute_quantity(
                        product_qty, line.product_id.uom_id
                    )
                qty_processed_per_product[line.product_id.id] += product_qty
            treated |= lines
        remaining = self - treated
        remaining.virtual_available_at_date = False
        remaining.scheduled_date = False
        remaining.forecast_expected_date = False
        remaining.free_qty_today = False
        remaining.qty_available_today = False

    @api.depends("product_id", "location_id", "product_id.route_ids")
    def _compute_is_mto(self):
        self.is_mto = False
        for line in self:
            if not line.display_qty_widget:
                continue
            product = line.product_id
            product_routes = product.route_ids + product.categ_id.total_route_ids

            # Check MTO
            warehouse = self.location_id.get_warehouse()
            mto_route = warehouse.mto_pull_id.route_id
            if not mto_route:
                try:
                    mto_route = self.env["stock.warehouse"]._find_global_route(
                        "stock.route_warehouse0_mto", _("Make To Order")
                    )
                except UserError:
                    # if route MTO not found in ir_model_data,
                    # we treat the product as in MTS
                    pass

            if mto_route and mto_route in product_routes:
                line.is_mto = True
            else:
                line.is_mto = False
