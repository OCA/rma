# Copyright 2021 Jarsa
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import api, fields, models
from odoo.tools import float_compare


class RepairOrder(models.Model):
    _inherit = "repair.order"

    procurement_group_id = fields.Many2one("procurement.group", copy=False)
    picking_ids = fields.One2many("stock.picking", "repair_id", string="Pickings")
    picking_count = fields.Integer(
        string="Delivery Orders", compute="_compute_picking_count"
    )

    @api.depends("picking_ids")
    def _compute_picking_count(self):
        for order in self:
            order.picking_count = len(order.picking_ids)

    def action_view_pickings(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock.action_picking_tree_all"
        )

        pickings = self.mapped("picking_ids")
        if len(pickings) > 1:
            action["domain"] = [("id", "in", pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref("stock.view_picking_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = pickings.id
        action["context"] = dict(
            self._context,
            default_picking_type_id=pickings[0].picking_type_id.id,
            default_origin=self.name,
            default_group_id=pickings[0].group_id.id,
        )
        return action

    def action_repair_confirm(self):
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        procurements = []
        for line in self.mapped("operations"):
            if line.product_id.type in ("consu", "service"):
                continue
            available_qty = self.env["stock.quant"]._get_available_quantity(
                line.product_id, line.location_id, strict=True
            )
            repair_qty = line.product_uom._compute_quantity(
                line.product_uom_qty, line.product_id.uom_id
            )
            if (
                float_compare(available_qty, repair_qty, precision_digits=precision)
                == 1
            ):
                continue
            group = line._get_procurement_group()
            values = line._prepare_procurement_values(group_id=group)
            product_qty, procurement_uom = line.product_uom._adjust_uom_quantities(
                line.product_uom_qty, line.product_id.uom_id
            )
            procurements.append(
                self.env["procurement.group"].Procurement(
                    line.product_id,
                    product_qty,
                    procurement_uom,
                    line.location_id,
                    line.name,
                    line.repair_id.name,
                    line.repair_id.company_id,
                    values,
                )
            )
        if procurements:
            self.env["procurement.group"].run(procurements)
        return super().action_repair_confirm()

    def action_repair_cancel(self):
        self.picking_ids.filtered(
            lambda p: p.state not in ["cancel", "done"]
        ).action_cancel()
        return super().action_repair_cancel()


class RepairOrderLine(models.Model):
    _inherit = "repair.line"

    def _get_procurement_group(self):
        self.ensure_one()
        if not self.repair_id.procurement_group_id:
            group = self.env["procurement.group"].create(
                self._prepare_procurement_group_vals()
            )
            self.repair_id.procurement_group_id = group
        return self.repair_id.procurement_group_id

    def _prepare_procurement_group_vals(self):
        self.ensure_one()
        return {
            "name": self.repair_id.name,
            "move_type": "direct",
            "repair_id": self.repair_id.id,
        }

    def _prepare_procurement_values(self, group_id=False):
        self.ensure_one()
        return {
            "group_id": group_id,
            "repair_line_id": self.id,
        }
