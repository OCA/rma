# Copyright 2020 Tecnativa - Ernesto Tejeda
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from copy import deepcopy

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero


class ReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    rma_operation_id = fields.Many2one(
        comodel_name="rma.operation",
        string="Operation",
        compute="_compute_rma_operation_id",
        store=True,
        readonly=False,
    )

    @api.depends("wizard_id.rma_operation_id")
    def _compute_rma_operation_id(self):
        for rec in self:
            if rec.wizard_id.rma_operation_id:
                rec.rma_operation_id = rec.wizard_id.rma_operation_id

    def _prepare_rma_vals(self):
        self.ensure_one()
        warehouse = self.move_id.picking_id.picking_type_id.warehouse_id
        return {
            "move_id": self.move_id.id,
            "product_id": self.move_id.product_id.id,
            "product_uom_qty": self.quantity,
            "product_uom": self.product_id.uom_id.id,
            "location_id": warehouse.rma_loc_id.id,
            "operation_id": self.rma_operation_id.id,
        }


class ReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    create_rma = fields.Boolean(string="Create RMAs")
    picking_type_code = fields.Selection(related="picking_id.picking_type_id.code")
    rma_operation_id = fields.Many2one(
        comodel_name="rma.operation",
        string="Requested operation",
    )

    @api.onchange("create_rma")
    def _onchange_create_rma(self):
        if self.create_rma:
            # We want to avoid setting the return move `to_refund` as it will change
            # the delivered quantities in the sale and set them to invoice.
            self.product_return_moves.to_refund = False

    def _prepare_rma_partner_values(self):
        self.ensure_one()
        partner = self.picking_id.partner_id
        partner_address = partner.address_get(["invoice", "delivery"])
        partner_invoice_id = partner_address.get("invoice", False)
        partner_shipping_id = partner_address.get("delivery", False)
        return (
            partner,
            partner_invoice_id and partner.browse(partner_invoice_id) or partner,
            partner_shipping_id and partner.browse(partner_shipping_id) or partner,
        )

    def _prepare_rma_vals(self):
        partner, partner_invoice, partner_shipping = self._prepare_rma_partner_values()
        origin = self.picking_id.name
        vals = self.env["rma"]._prepare_procurement_group_vals()
        vals["partner_id"] = partner_shipping.id
        vals["name"] = origin
        group = self.env["procurement.group"].create(vals)
        return {
            "user_id": self.env.user.id,
            "partner_id": partner.id,
            "partner_shipping_id": partner_shipping.id,
            "partner_invoice_id": partner_invoice.id,
            "origin": origin,
            "picking_id": self.picking_id.id,
            "company_id": self.company_id.id,
            "procurement_group_id": group.id,
        }

    def _prepare_rma_vals_list(self):
        vals_list = []
        for return_picking in self:
            global_vals = return_picking._prepare_rma_vals()
            for line in return_picking.product_return_moves:
                if not line.move_id or float_is_zero(
                    line.quantity, precision_rounding=line.uom_id.rounding
                ):
                    continue
                vals = deepcopy(global_vals)
                vals.update(line._prepare_rma_vals())
                vals_list.append(vals)
        return vals_list

    def action_create_returns(self):
        """Override create_returns method for creating one or more
        'confirmed' RMAs after return a delivery picking in case
        'Create RMAs' checkbox is checked in this wizard.
        New RMAs will be linked to the delivery picking as the origin
        delivery and also RMAs will be linked to the returned picking
        as the 'Receipt'.
        """
        if self.create_rma:
            if not self.picking_id.partner_id:
                raise ValidationError(
                    self.env._(
                        "You must specify the 'Customer' in the "
                        "'Stock Picking' from which RMAs will be created"
                    )
                )
            vals_list = self._prepare_rma_vals_list()
            rmas = self.env["rma"].create(vals_list)
            rmas.action_confirm()
            picking = rmas.reception_move_id.picking_id
            picking = picking and picking[0] or picking
            ctx = dict(self.env.context)
            ctx.update(
                {
                    "default_partner_id": picking.partner_id.id,
                    "search_default_picking_type_id": picking.picking_type_id.id,
                    "search_default_draft": False,
                    "search_default_assigned": False,
                    "search_default_confirmed": False,
                    "search_default_ready": False,
                    "search_default_planning_issues": False,
                    "search_default_available": False,
                }
            )
            return {
                "name": self.env._("Returned Picking"),
                "view_mode": "form,list,calendar",
                "res_model": "stock.picking",
                "res_id": picking.id,
                "type": "ir.actions.act_window",
                "context": ctx,
            }
        return super().action_create_returns()
