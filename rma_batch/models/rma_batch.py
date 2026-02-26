# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RmaBatch(models.Model):
    _name = "rma.batch"
    _description = "RMA Batch"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
    )
    date = fields.Datetime(
        default=fields.Datetime.now,
        index=True,
        required=True,
    )
    partner_id = fields.Many2one("res.partner", string="Customer", required=True)
    partner_shipping_id = fields.Many2one(
        string="Shipping Address",
        comodel_name="res.partner",
        help="Shipping address for current RMA.",
        compute="_compute_partner_shipping_id",
        store=True,
        readonly=False,
    )
    partner_invoice_id = fields.Many2one(
        string="Invoice Address",
        comodel_name="res.partner",
        domain=(
            "['|', ('company_id', '=', False), ('company_id', '='," " company_id)]"
        ),
        help="Refund address for current RMA.",
        compute="_compute_partner_invoice_id",
        store=True,
        readonly=False,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible",
        index=True,
        tracking=True,
        default=lambda self: self.env.user,
    )
    team_id = fields.Many2one(
        comodel_name="rma.team",
        string="RMA team",
        index=True,
        compute="_compute_team_id",
        store=True,
    )
    tag_ids = fields.Many2many(comodel_name="rma.tag", string="Tags")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("ready", "Ready"),
            ("confirmed", "Confirmed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        help=(
            "Represents the preparation and validation progress of the RMA batch:\n"
            "- Draft: The batch is being prepared. RMAs can still be added or edited.\n"
            "- Ready: All required information for the batch and its RMAs is complete. "
            "The batch is ready to be confirmed.\n"
            "- Confirmed: The batch has been validated and all linked RMAs are "
            "confirmed.\n"
            "- Cancelled: The batch and its related RMAs are cancelled or ignored."
        ),
    )
    rma_ids = fields.One2many("rma", "batch_id", string="RMA")
    count_rma = fields.Integer(compute="_compute_count_rma")
    operation_id = fields.Many2one(
        comodel_name="rma.operation", string="Requested operation"
    )
    location_id = fields.Many2one(
        comodel_name="stock.location",
        domain=lambda self: self.env["rma"]._domain_location_id(),
        help="Default RMA location that will be propagated to RMA order lines",
    )

    @api.depends("rma_ids")
    def _compute_count_rma(self):
        for rec in self:
            rec.count_rma = len(rec.rma_ids)

    @api.depends("partner_id")
    def _compute_partner_shipping_id(self):
        self.partner_shipping_id = False
        for record in self.filtered("partner_id"):
            address = record.partner_id.address_get(["delivery"])
            record.partner_shipping_id = address.get("delivery", False)

    @api.depends("partner_id")
    def _compute_partner_invoice_id(self):
        self.partner_invoice_id = False
        for record in self.filtered("partner_id"):
            address = record.partner_id.address_get(["invoice"])
            record.partner_invoice_id = address.get("invoice", False)

    @api.depends("user_id")
    def _compute_team_id(self):
        self.team_id = False
        for record in self.filtered("user_id"):
            record.team_id = (
                self.env["rma.team"]
                .sudo()
                .search(
                    [
                        "|",
                        ("user_id", "=", record.user_id.id),
                        ("member_ids", "=", record.user_id.id),
                        "|",
                        ("company_id", "=", False),
                        ("company_id", "child_of", record.company_id.ids),
                    ],
                    limit=1,
                )
            )

    def action_draft(self):
        self.rma_ids.action_draft()
        self.write({"state": "draft"})

    def action_confirm(self):
        self.rma_ids.action_confirm()
        self.write({"state": "confirmed"})

    def action_ready(self):
        self.write({"state": "ready"})

    def action_cancel(self):
        self.rma_ids.action_cancel()
        self.write({"state": "cancelled"})

    def action_open_rma(self):
        self.ensure_one()
        return {
            "name": _("RMA"),
            "type": "ir.actions.act_window",
            "res_model": "rma",
            "view_mode": "list,form",
            "domain": [("batch_id", "=", self.id)],
            "context": {"default_batch_id": self.id},
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("rma.batch")
        return super().create(vals_list)

    @api.ondelete(at_uninstall=False)
    def _unlink_only_draft_rmas(self):
        if self.rma_ids.filtered(lambda r: r.state != "draft"):
            raise ValidationError(
                self.env._("You cannot delete RMAs that are not in draft state")
            )
        return super().unlink()
