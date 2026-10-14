# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Command


class RmaBatch(models.Model):
    _inherit = "rma.batch"

    receipt_group_id = fields.Many2one(
        comodel_name="procurement.group",
    )
    receipt_ids = fields.One2many(
        comodel_name="stock.picking", inverse_name="rma_batch_id"
    )
    refund_ids = fields.Many2many(
        comodel_name="account.move",
        compute="_compute_refund_ids",
    )
    count_refunds = fields.Integer(
        compute="_compute_count_refunds",
    )
    new_receipt_button_visible = fields.Boolean(
        compute="_compute_new_receipt_button_visible",
    )
    can_be_refunded = fields.Boolean(
        compute="_compute_can_be_refunded",
    )
    count_receipts = fields.Integer(compute="_compute_count_receipts")

    @api.depends("rma_ids.refund_id")
    def _compute_refund_ids(self):
        for batch in self:
            batch.refund_ids = batch.rma_ids.refund_id

    @api.depends("refund_ids")
    def _compute_count_refunds(self):
        for batch in self:
            batch.count_refunds = len(batch.refund_ids)

    @api.depends("receipt_ids")
    def _compute_count_receipts(self):
        fetch_data = self.env["stock.picking"].read_group(
            [("rma_batch_id", "in", self.ids)],
            fields=["rma_batch_id"],
            groupby="rma_batch_id",
        )
        result = {
            data["rma_batch_id"][0]: data["rma_batch_id_count"] for data in fetch_data
        }
        for batch in self:
            batch.count_receipts = result.get(batch.id, 0)

    @api.depends("state", "receipt_ids")
    def _compute_new_receipt_button_visible(self):
        for batch in self:
            if batch.state != "draft":
                batch.new_receipt_button_visible = False
            else:
                if any(receipt.state == "draft" for receipt in batch.receipt_ids):
                    batch.new_receipt_button_visible = False
                else:
                    batch.new_receipt_button_visible = True

    @api.depends("rma_ids.can_be_refunded")
    def _compute_can_be_refunded(self):
        for batch in self:
            if batch.rma_ids:
                batch.can_be_refunded = all(
                    rma.can_be_refunded for rma in batch.rma_ids
                )
            else:
                batch.can_be_refunded = False

    def action_view_refunds(self):
        """Invoked when 'Refunds' smart button in rma batch form view is clicked."""
        self.ensure_one()
        action = {
            "name": self.env._("Refund(s)"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "target": "current",
        }
        invoice_ids = self.refund_ids.ids
        if len(invoice_ids) == 1:
            invoice = invoice_ids[0]
            action["res_id"] = invoice
            action["view_mode"] = "form"
            action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
        else:
            action["view_mode"] = "list,form"
            action["domain"] = [("id", "in", invoice_ids)]
        return action

    def action_view_receipts(self):
        self.ensure_one()

        form_view_ref = self.env.ref("stock.view_picking_form", False)
        list_view_ref = self.env.ref("stock.vpicktree", False)

        result = self.env["ir.actions.act_window"]._for_xml_id(
            "stock.action_picking_tree_all"
        )
        result.update(
            {
                "domain": [("id", "in", self.receipt_ids.ids)],
                "views": [(list_view_ref.id, "list"), (form_view_ref.id, "form")],
            }
        )
        return result

    def action_refund(self):
        return self.rma_ids.action_refund()

    def _get_reception_group(self):
        return self.env["procurement.group"].create({"name": self.name})

    def _get_default_warehouse(self):
        if self.location_id:
            return self.location_id.warehouse_id
        else:
            return self.env["stock.warehouse"].search(
                [("company_id", "=", self.env.company.id)], limit=1
            )

    def _get_new_picking_values(self):
        return {
            "partner_id": self.partner_id.id,
            "group_id": self.receipt_group_id.id,
            "picking_type_id": self._get_default_picking_type().id,
            "rma_batch_id": self.id,
        }

    def _get_default_picking_type(self):
        return self._get_default_warehouse().rma_in_type_id

    def action_create_blank_return_picking(self):
        """
        Create a blank return picking to prepare the reception work (essentially to
        fill in the customer)
        """
        self.ensure_one()
        draft_pickings = self.receipt_ids.filtered(
            lambda picking: picking.state == "draft"
        )
        if draft_pickings:
            raise ValidationError(
                self.env._(
                    "There is already a draft picking: %(picking_name)s",
                    picking_name=",".join(draft_pickings.mapped("display_name")),
                )
            )
        picking = self.env["stock.picking"].create(self._get_new_picking_values())
        message = self.env._(
            "The picking %(picking_name)s has been created!",
            picking_name=picking.display_name,
        )
        title = self.env._("New picking created")
        self.env.user.notify_success(
            message,
            title,
        )

    def _prepare_new_batch_from_rma_vals(self, rmas):
        if not rmas:
            ValidationError(self.env._("You cannot create batch without RMAs!"))
        first_rma = next(iter(rmas))
        return {
            "partner_id": first_rma.partner_id.id,
            "user_id": first_rma.user_id.id or self.env.user.id,
            "team_id": first_rma.team_id.id if first_rma.team_id else False,
            "tag_ids": [Command.set(first_rma.tag_ids.ids)]
            if first_rma.tag_ids
            else [],
            "state": "draft",
            "operation_id": first_rma.operation_id.id,
            "rma_ids": [Command.set(rmas.ids)],
        }

    @api.model
    def _create_and_assign_rma(self, rmas):
        # If the return picking was created manually, assign new rmas to a new batch
        if any(rma.batch_id for rma in rmas):
            # Batch is already assigned to RMA (e.g.: We created the picking through
            # the batch directly).
            return next(iter(rmas)).batch_id
        batch = self.env["rma.batch"].create(
            self._prepare_new_batch_from_rma_vals(rmas)
        )
        return batch
