# Copyright 2020 Tecnativa - Ernesto Tejeda
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict
from copy import deepcopy
from itertools import groupby

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form
from odoo.tools import html2plaintext

from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES

from .rma_operation import TIMING_AFTER_RECEIPT, TIMING_ON_CONFIRM


class Rma(models.Model):
    _name = "rma"
    _description = "RMA"
    _order = "date desc, priority"
    _inherit = ["mail.thread", "portal.mixin", "mail.activity.mixin"]

    def _domain_location_id(self):
        # this is done with sudo, intercompany rules are not applied by default so we
        # add company in domain explicitly to avoid multi-company rule error when
        # the user will try to choose a location
        rma_loc = (
            self.env["stock.warehouse"]
            .search([("company_id", "in", self.env.companies.ids)])
            .mapped("rma_loc_id")
        )
        return [("id", "child_of", rma_loc.ids)]

    # General fields
    sent = fields.Boolean()
    name = fields.Char(
        string="Name",
        index=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
        default=lambda self: _("New"),
    )
    origin = fields.Char(
        string="Source Document",
        states={"locked": [("readonly", True)], "cancelled": [("readonly", True)]},
        help="Reference of the document that generated this RMA.",
    )
    date = fields.Datetime(
        default=lambda self: fields.Datetime.now(),
        index=True,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    deadline = fields.Date(
        states={"locked": [("readonly", True)], "cancelled": [("readonly", True)]},
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Responsible",
        index=True,
        tracking=True,
        states={"locked": [("readonly", True)], "cancelled": [("readonly", True)]},
    )
    team_id = fields.Many2one(
        comodel_name="rma.team",
        string="RMA team",
        index=True,
        states={"locked": [("readonly", True)], "cancelled": [("readonly", True)]},
    )
    tag_ids = fields.Many2many(comodel_name="rma.tag", string="Tags")
    finalization_id = fields.Many2one(
        string="Finalization Reason",
        comodel_name="rma.finalization",
        copy=False,
        readonly=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
        states={"locked": [("readonly", True)], "cancelled": [("readonly", True)]},
    )
    partner_id = fields.Many2one(
        string="Customer",
        comodel_name="res.partner",
        readonly=True,
        states={"draft": [("readonly", False)]},
        index=True,
        tracking=True,
    )
    partner_shipping_id = fields.Many2one(
        string="Shipping Address",
        comodel_name="res.partner",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Shipping address for current RMA.",
    )
    partner_invoice_id = fields.Many2one(
        string="Invoice Address",
        comodel_name="res.partner",
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Refund address for current RMA.",
    )
    commercial_partner_id = fields.Many2one(
        comodel_name="res.partner",
        related="partner_id.commercial_partner_id",
    )
    picking_id = fields.Many2one(
        comodel_name="stock.picking",
        string="Origin Delivery",
        domain="["
        "    ('state', '=', 'done'),"
        "    ('picking_type_id.code', '=', 'outgoing'),"
        "    ('partner_id', 'child_of', commercial_partner_id),"
        "]",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    move_id = fields.Many2one(
        comodel_name="stock.move",
        string="Origin move",
        domain="["
        "    ('picking_id', '=', picking_id),"
        "    ('picking_id', '!=', False)"
        "]",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        domain=[("type", "in", ["consu", "product"])],
    )
    product_uom_qty = fields.Float(
        string="Quantity",
        required=True,
        default=1.0,
        digits="Product Unit of Measure",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    product_uom = fields.Many2one(
        comodel_name="uom.uom",
        string="UoM",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: self.env.ref("uom.product_uom_unit").id,
    )
    procurement_group_id = fields.Many2one(
        comodel_name="procurement.group",
        string="Procurement group",
        readonly=True,
        states={
            "draft": [("readonly", False)],
            "confirmed": [("readonly", False)],
            "received": [("readonly", False)],
        },
    )
    priority = fields.Selection(
        string="Priority",
        selection=PROCUREMENT_PRIORITIES,
        default="1",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    operation_id = fields.Many2one(
        "rma.operation",
        "Requested operation",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("received", "Received"),
            ("waiting_return", "Waiting for return"),
            ("waiting_replacement", "Waiting for replacement"),
            ("refunded", "Refunded"),
            ("returned", "Returned"),
            ("replaced", "Replaced"),
            ("finished", "Finished"),
            ("locked", "Locked"),
            ("cancelled", "Canceled"),
        ],
        default="draft",
        copy=False,
        tracking=True,
    )
    description = fields.Html(
        states={"locked": [("readonly", True)], "cancelled": [("readonly", True)]},
    )
    # Reception fields
    location_id = fields.Many2one(
        comodel_name="stock.location",
        domain=_domain_location_id,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        compute="_compute_warehouse_id",
        store=True,
    )
    reception_move_ids = fields.Many2many(
        "stock.move",
        string="Reception move",
        copy=False,
    )
    # Keep for backwards compatibility
    reception_move_id = fields.Many2one(
        "stock.move", "Reception move", compute="_compute_reception_move"
    )
    can_be_receipted = fields.Boolean(compute="_compute_can_be_receipted")
    # Refund fields
    refund_id = fields.Many2one(
        comodel_name="account.move",
        string="Refund",
        readonly=True,
        copy=False,
    )
    refund_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Refund line",
        readonly=True,
        copy=False,
    )
    can_be_refunded = fields.Boolean(compute="_compute_can_be_refunded")
    # Delivery fields
    delivery_move_ids = fields.One2many(
        comodel_name="stock.move",
        inverse_name="rma_id",
        string="Delivery reservation",
        readonly=True,
        copy=False,
    )
    delivery_picking_count = fields.Integer(
        string="Delivery count",
        compute="_compute_delivery_picking_count",
    )
    delivered_qty = fields.Float(
        string="Delivered qty",
        digits="Product Unit of Measure",
        compute="_compute_delivered_qty",
        store=True,
    )
    delivered_qty_done = fields.Float(
        string="Delivered qty done",
        digits="Product Unit of Measure",
        compute="_compute_delivered_qty",
        compute_sudo=True,
    )
    can_be_returned = fields.Boolean(
        compute="_compute_can_be_returned",
    )
    can_be_replaced = fields.Boolean(
        compute="_compute_can_be_replaced",
    )
    can_be_locked = fields.Boolean(
        compute="_compute_can_be_locked",
    )
    can_be_finished = fields.Boolean(
        compute="_compute_can_be_finished",
    )
    remaining_qty = fields.Float(
        string="Remaining delivered qty",
        digits="Product Unit of Measure",
        compute="_compute_remaining_qty",
    )
    remaining_qty_to_done = fields.Float(
        string="Remaining delivered qty to done",
        digits="Product Unit of Measure",
        compute="_compute_remaining_qty",
    )
    uom_category_id = fields.Many2one(
        related="product_id.uom_id.category_id", string="Category UoM"
    )
    # Split fields
    can_be_split = fields.Boolean(
        compute="_compute_can_be_split",
    )
    origin_split_rma_id = fields.Many2one(
        comodel_name="rma",
        string="Extracted from",
        readonly=True,
        copy=False,
    )

    def _compute_delivery_picking_count(self):
        for rma in self:
            rma.delivery_picking_count = len(rma.delivery_move_ids.picking_id)

    @api.depends("reception_move_ids")
    def _compute_reception_move(self):
        for rma in self:
            rma.reception_move_id = rma.reception_move_ids[:1]

    @api.depends(
        "delivery_move_ids",
        "delivery_move_ids.state",
        "delivery_move_ids.scrapped",
        "delivery_move_ids.product_uom_qty",
        "delivery_move_ids.reserved_availability",
        "delivery_move_ids.quantity_done",
        "delivery_move_ids.product_uom",
        "product_uom",
    )
    def _compute_delivered_qty(self):
        """Compute 'delivered_qty' and 'delivered_qty_done' fields.

        delivered_qty: represents the quantity delivery or to be
        delivery. For each move in delivery_move_ids the quantity done
        is taken, if it is empty the reserved quantity is taken,
        otherwise the initial demand is taken.

        delivered_qty_done: represents the quantity delivered and done.
        For each 'done' move in delivery_move_ids the quantity done is
        taken. This field is used to control when the RMA cam be set
        to 'delivered' state.
        """
        for record in self:
            delivered_qty = 0.0
            delivered_qty_done = 0.0
            for move in record.delivery_move_ids.filtered(
                lambda r: r.state != "cancel" and not r.scrapped
            ):
                if move.quantity_done:
                    quantity_done = move.product_uom._compute_quantity(
                        move.quantity_done, record.product_uom
                    )
                    if move.state == "done":
                        delivered_qty_done += quantity_done
                    delivered_qty += quantity_done
                elif move.reserved_availability:
                    delivered_qty += move.product_uom._compute_quantity(
                        move.reserved_availability, record.product_uom
                    )
                elif move.product_uom_qty:
                    delivered_qty += move.product_uom._compute_quantity(
                        move.product_uom_qty, record.product_uom
                    )
            record.delivered_qty = delivered_qty
            record.delivered_qty_done = delivered_qty_done

    @api.depends("product_uom_qty", "delivered_qty", "delivered_qty_done")
    def _compute_remaining_qty(self):
        """Compute 'remaining_qty' and 'remaining_qty_to_done' fields.

        remaining_qty: is used to set a default quantity of replacing
        or returning of product to the customer.

        remaining_qty_to_done: the aim of this field to control when the
        RMA cam be set to 'delivered' state. An RMA with
        remaining_qty_to_done <= 0 can be set to 'delivery'. It is used
        in stock.move._action_done method of stock.move and
        rma.extract_quantity.
        """
        for r in self:
            r.remaining_qty = r.product_uom_qty - r.delivered_qty
            r.remaining_qty_to_done = r.product_uom_qty - r.delivered_qty_done

    @api.depends(
        "state",
        "operation_id",
        "operation_id.create_receipt_timing",
    )
    def _compute_can_be_receipted(self):
        for rma in self:
            operation = rma.operation_id
            rma.can_be_receipted = rma.state == "draft" and (
                not operation or operation.create_receipt_timing == TIMING_ON_CONFIRM
            )

    @api.depends(
        "state",
        "operation_id",
        "operation_id.create_refund_timing",
    )
    def _compute_can_be_refunded(self):
        """Compute 'can_be_refunded'. This field controls the visibility
        of 'Refund' button in the rma form view and determinates if
        an rma can be refunded. It is used in rma.action_refund method.
        """
        for rma in self:
            can_be_refunded = False
            state = rma.state
            operation = rma.operation_id
            if state == "received":
                if (
                    not operation
                    or operation.create_refund_timing == TIMING_AFTER_RECEIPT
                ):
                    can_be_refunded = True
            elif (
                state == "draft" and operation.create_refund_timing == TIMING_ON_CONFIRM
            ):
                can_be_refunded = True
            rma.can_be_refunded = can_be_refunded

    @api.depends(
        "remaining_qty",
        "state",
        "operation_id",
        "operation_id.create_return_timing",
    )
    def _compute_can_be_returned(self):
        """Compute 'can_be_returned'. This field controls the visibility
        of the 'Return to customer' button in the rma form
        view and determinates if an rma can be returned to the customer.
        This field is used in:
        rma._compute_can_be_split
        rma._ensure_can_be_returned.
        """
        for rma in self:
            can_be_returned = False
            state = rma.state
            operation = rma.operation_id
            if (
                state in ["received", "waiting_return"]
                and rma.remaining_qty > 0
                and (
                    not operation
                    or operation.create_return_timing == TIMING_AFTER_RECEIPT
                )
            ):
                can_be_returned = True
            elif (
                state == "draft" and operation.create_return_timing == TIMING_ON_CONFIRM
            ):
                can_be_returned = True
            rma.can_be_returned = can_be_returned

    @api.depends("state")
    def _compute_can_be_replaced(self):
        """Compute 'can_be_replaced'. This field controls the visibility
        of 'Replace' button in the rma form
        view and determinates if an rma can be replaced.
        This field is used in:
        rma._compute_can_be_split
        rma._ensure_can_be_replaced.
        """
        for rma in self:
            rma.can_be_replaced = rma.state in [
                "received",
                "waiting_replacement",
                "replaced",
            ]

    @api.depends("state", "remaining_qty")
    def _compute_can_be_finished(self):
        for rma in self:
            rma.can_be_finished = (
                rma.state in {"received", "waiting_replacement", "waiting_return"}
                and rma.remaining_qty > 0
            )

    @api.depends("product_uom_qty", "state", "remaining_qty", "remaining_qty_to_done")
    def _compute_can_be_split(self):
        """Compute 'can_be_split'. This field controls the
        visibility of 'Split' button in the rma form view and
        determinates if an rma can be split.
        This field is used in:
        rma._ensure_can_be_split
        """
        for r in self:
            if r.product_uom_qty > 1 and (
                (r.state == "waiting_return" and r.remaining_qty > 0)
                or (r.state == "waiting_replacement" and r.remaining_qty_to_done > 0)
            ):
                r.can_be_split = True
            else:
                r.can_be_split = False

    @api.depends("remaining_qty_to_done", "state")
    def _compute_can_be_locked(self):
        for r in self:
            r.can_be_locked = r.remaining_qty_to_done > 0 and r.state in [
                "received",
                "waiting_return",
                "waiting_replacement",
            ]

    @api.depends("location_id")
    def _compute_warehouse_id(self):
        for rma in self:
            if rma.location_id:
                rma.warehouse_id = self.env["stock.warehouse"].search(
                    [("rma_loc_id", "parent_of", rma.location_id.id)], limit=1
                )

    def _compute_access_url(self):
        for record in self:
            record.access_url = "/my/rmas/{}".format(record.id)

    # Constrains methods (@api.constrains)
    @api.constrains(
        "state", "partner_id", "partner_shipping_id", "partner_invoice_id", "product_id"
    )
    def _check_required_after_draft(self):
        """Check that RMAs are being created or edited with the
        necessary fields filled out. Only applies to 'Draft' and
        'Cancelled' states.
        """
        rma = self.filtered(lambda r: r.state not in ["draft", "cancelled"])
        rma._ensure_required_fields()

    # onchange methods (@api.onchange)
    @api.onchange("user_id")
    def _onchange_user_id(self):
        if self.user_id:
            self.team_id = (
                self.env["rma.team"]
                .sudo()
                .search(
                    [
                        "|",
                        ("user_id", "=", self.user_id.id),
                        ("member_ids", "=", self.user_id.id),
                        "|",
                        ("company_id", "=", False),
                        ("company_id", "child_of", self.company_id.ids),
                    ],
                    limit=1,
                )
            )
        else:
            self.team_id = False

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        self.picking_id = False
        partner_invoice_id = False
        partner_shipping_id = False
        if self.partner_id:
            address = self.partner_id.address_get(["invoice", "delivery"])
            partner_invoice_id = address.get("invoice", False)
            partner_shipping_id = address.get("delivery", False)
        self.partner_invoice_id = partner_invoice_id
        self.partner_shipping_id = partner_shipping_id

    @api.onchange("picking_id")
    def _onchange_picking_id(self):
        location = False
        if self.picking_id:
            warehouse = self.picking_id.picking_type_id.warehouse_id
            location = warehouse.rma_loc_id.id
        self.location_id = location
        self.move_id = False
        self.product_id = False

    @api.onchange("move_id")
    def _onchange_move_id(self):
        if self.move_id:
            self.product_id = self.move_id.product_id
            self.product_uom_qty = self.move_id.product_uom_qty
            self.product_uom = self.move_id.product_uom

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            # Set UoM
            if not self.product_uom or self.product_id.uom_id.id != self.product_uom.id:
                self.product_uom = self.product_id.uom_id
            # Set stock location (location_id)
            user = self.env.user
            if (
                not user.has_group("stock.group_stock_multi_locations")
                and not self.location_id
            ):
                # If this condition is True, it is because a picking is not set
                company = self.company_id or self.env.company
                warehouse = self.env["stock.warehouse"].search(
                    [("company_id", "=", company.id)], limit=1
                )
                self.location_id = warehouse.rma_loc_id.id

    # CRUD methods (ORM overrides)
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                ir_sequence = self.env["ir.sequence"]
                if "company_id" in vals:
                    ir_sequence = ir_sequence.with_company(vals["company_id"])
                vals["name"] = ir_sequence.next_by_code("rma")
            # Assign a default team_id which will be the first in the sequence
            if not vals.get("team_id"):
                vals["team_id"] = self.env["rma.team"].search([], limit=1).id
        rmas = super().create(vals_list)
        # Send acknowledge when the RMA is created from the portal and the
        # company has the proper setting active. This context is set by the
        # `rma_sale` module.
        if self.env.context.get("from_portal"):
            rmas._send_draft_email()
        return rmas

    def copy(self, default=None):
        team = super().copy(default)
        for follower in self.message_follower_ids:
            team.message_subscribe(
                partner_ids=follower.partner_id.ids,
                subtype_ids=follower.subtype_ids.ids,
            )
        return team

    def unlink(self):
        if self.filtered(lambda r: r.state != "draft"):
            raise ValidationError(
                _("You cannot delete RMAs that are not in draft state")
            )
        return super().unlink()

    def _send_draft_email(self):
        """Send customer notifications they place the RMA from the portal"""
        for rma in self.filtered("company_id.send_rma_draft_confirmation"):
            rma_template_id = rma.company_id.rma_mail_draft_confirmation_template_id.id
            rma.with_context(
                force_send=True,
                mark_rma_as_sent=True,
                default_subtype_id=self.env.ref("rma.mt_rma_notification").id,
            ).message_post_with_template(rma_template_id)

    def _send_confirmation_email(self):
        """Auto send notifications"""
        subtype = self.env.ref("rma.mt_rma_notification")
        for rma in self:
            if not rma.company_id.send_rma_confirmation:
                continue
            rma_template_id = rma.company_id.rma_mail_confirmation_template_id.id
            rma.with_context(
                force_send=True,
                mark_rma_as_sent=True,
                default_subtype_id=subtype.id,
            ).message_post_with_template(rma_template_id)

    def _send_receipt_confirmation_email(self):
        """Send customer notifications when the products are received"""
        for rma in self.filtered("company_id.send_rma_receipt_confirmation"):
            rma_template_id = (
                rma.company_id.rma_mail_receipt_confirmation_template_id.id
            )
            rma.with_context(
                force_send=True,
                mark_rma_as_sent=True,
                default_subtype_id=self.env.ref("rma.mt_rma_notification").id,
            ).message_post_with_template(rma_template_id)

    # Action methods
    def action_rma_send(self):
        self.ensure_one()
        template = self.env.ref("rma.mail_template_rma_notification", False)
        template = self.company_id.rma_mail_confirmation_template_id or template
        form = self.env.ref("mail.email_compose_message_wizard_form", False)
        ctx = {
            "default_model": "rma",
            "default_subtype_id": self.env.ref("rma.mt_rma_notification").id,
            "default_res_id": self.ids[0],
            "default_use_template": bool(template),
            "default_template_id": template and template.id or False,
            "default_composition_mode": "comment",
            "mark_rma_as_sent": True,
            "model_description": "RMA",
            "force_email": True,
        }
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(form.id, "form")],
            "view_id": form.id,
            "target": "new",
            "context": ctx,
        }

    def _add_message_subscribe_partner(self):
        for rma in self:
            if rma.partner_id and rma.partner_id not in rma.message_partner_ids:
                rma.message_subscribe([rma.partner_id.id])

    def _product_is_storable(self, product=None):
        product = product or self.product_id
        return product.type in ["product", "consu"]

    def _prepare_procurement_group_values(self):
        return {
            "move_type": "direct",
            "partner_id": self and self.partner_shipping_id.id or False,
            "name": self and ", ".join(self.mapped("name")) or False,
        }

    def _create_procurement_group(self, values=None):
        vals = self._prepare_procurement_group_values()
        if values:
            vals.update(values)
        return self.env["procurement.group"].create(vals)

    def _prepare_procurement_values(
        self, warehouse=None, scheduled_date=None, group=None
    ):
        self.ensure_one()
        group = group or self.procurement_group_id or self._create_procurement_group()
        return {
            "company_id": self.company_id,
            "group_id": group,
            "date_planned": scheduled_date or fields.Datetime.now(),
            "warehouse_id": warehouse or self.warehouse_id,
            "partner_id": group.partner_id.id,
            "priority": self.priority,
        }

    def _prepare_procurement(
        self,
        location,
        values,
        product=None,
        qty=None,
        uom=None,
    ):
        self.ensure_one()
        group = values.get("group_id")
        product = product or self.product_id
        if not qty:
            qty = self.product_uom_qty
            uom = self.product_uom
        return self.env["procurement.group"].Procurement(
            product,
            qty,
            uom,
            location,
            product.display_name,
            group.name,
            self.company_id,
            values,
        )

    def _prepare_reception_procurement_values(self, group=None):
        values = self._prepare_procurement_values(group=group)
        values.update(
            {
                "rma_receiver_ids": [(6, 0, self.ids)],
            }
        )
        if self.move_id:
            values.update(
                {
                    "origin_returned_move_id": self.move_id.id,
                }
            )
        return values

    def _prepare_reception_procurement_group_values(self):
        self.ensure_one()
        return {}

    def _create_reception_procurement_group(self):
        return self._create_procurement_group(
            self._prepare_reception_procurement_group_values()
        )

    def _prepare_reception_procurement(self):
        self.ensure_one()
        group = self.procurement_group_id
        if not group:
            group = self._create_reception_procurement_group()
        values = self._prepare_reception_procurement_values(group)
        return self._prepare_procurement(self.location_id, values)

    def _prepare_reception_procurements(self):
        procurements = []
        for rma in self:
            if not rma._product_is_storable():
                continue
            procurements.append(rma._prepare_reception_procurement())
        return procurements

    def _run_procurements(self, procurements):
        if procurements:
            self.env["procurement.group"].run(procurements)

    def _create_receptions(self):
        procurements = self._prepare_reception_procurements()
        self._run_procurements(procurements)

    def _post_process_create_receptions(self):
        pickings = self.reception_move_ids.picking_id
        if pickings:
            pickings.action_assign()

    def create_receptions(self):
        self = self.filtered(lambda rma: rma.can_be_receipted)
        self._create_receptions()
        self._post_process_create_receptions()

    def action_confirm(self):
        """Invoked when 'Confirm' button in rma form view is clicked."""
        self._ensure_required_fields()
        self = self.filtered(lambda rma: rma.state == "draft")
        if not self:
            return
        self.create_receptions()
        self.create_deliveries(set_state=False)
        self.action_refund(set_state=False)
        self.write({"state": "confirmed"})
        self._add_message_subscribe_partner()
        self._send_confirmation_email()

    def action_refund(self, set_state=True):
        """Invoked when 'Refund' button in rma form view is clicked
        and 'rma_refund_action_server' server action is run.
        """
        vals = {}
        if set_state:
            vals["state"] = "refunded"
        group_dict = {}
        for record in self.filtered("can_be_refunded"):
            key = (record.partner_invoice_id.id, record.company_id.id)
            group_dict.setdefault(key, self.env["rma"])
            group_dict[key] |= record
        for rmas in group_dict.values():
            origin = ", ".join(rmas.mapped("name"))
            invoice_form = Form(
                self.env["account.move"]
                .sudo()
                .with_context(
                    default_move_type="out_refund",
                    company_id=rmas[0].company_id.id,
                ),
                "account.view_move_form",
            )
            rmas[0]._prepare_refund(invoice_form, origin)
            refund = invoice_form.save()
            for rma in rmas:
                # For each iteration the Form is edited, a new invoice line
                # is added and then saved. This is to generate the other
                # lines of the accounting entry and to specify the associated
                # RMA to that new invoice line.
                invoice_form = Form(refund)
                with invoice_form.invoice_line_ids.new() as line_form:
                    rma._prepare_refund_line(line_form)
                refund = invoice_form.save()
                line = refund.invoice_line_ids.filtered(lambda r: not r.rma_id)
                line.rma_id = rma.id
                _vals = deepcopy(vals)
                _vals.update(
                    {
                        "refund_line_id": line.id,
                        "refund_id": refund.id,
                    }
                )
                rma.write(_vals)
            refund.invoice_origin = origin
            refund.with_user(self.env.uid).message_post_with_view(
                "mail.message_origin_link",
                values={"self": refund, "origin": rmas},
                subtype_id=self.env.ref("mail.mt_note").id,
            )

    def action_replace(self):
        """Invoked when 'Replace' button in rma form view is clicked."""
        self.ensure_one()
        self._ensure_can_be_replaced()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "rma.rma_delivery_wizard_action"
        )
        action["name"] = "Replace product(s)"
        action["context"] = dict(self.env.context)
        action["context"].update(
            active_id=self.id,
            active_ids=self.ids,
            rma_delivery_type="replace",
        )
        return action

    def action_return(self):
        """Invoked when 'Return to customer' button in rma form
        view is clicked.
        """
        self.ensure_one()
        self._ensure_can_be_returned()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "rma.rma_delivery_wizard_action"
        )
        action["context"] = dict(self.env.context)
        action["context"].update(
            active_id=self.id,
            active_ids=self.ids,
            rma_delivery_type="return",
        )
        return action

    def action_split(self):
        """Invoked when 'Split' button in rma form view is clicked."""
        self.ensure_one()
        self._ensure_can_be_split()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "rma.rma_split_wizard_action"
        )
        action["context"] = dict(self.env.context)
        action["context"].update(active_id=self.id, active_ids=self.ids)
        return action

    def action_finish(self):
        """Invoked when a user wants to manually finalize the RMA"""
        self.ensure_one()
        self._ensure_can_be_returned()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "rma.rma_finalization_wizard_action"
        )
        action["context"] = dict(self.env.context)
        action["context"].update(active_id=self.id, active_ids=self.ids)
        return action

    def action_cancel(self):
        """Invoked when 'Cancel' button in rma form view is clicked."""
        self.reception_move_ids._action_cancel()
        self.write({"state": "cancelled"})

    def action_draft(self):
        cancelled_rma = self.filtered(lambda r: r.state == "cancelled")
        cancelled_rma.write({"state": "draft"})

    def action_lock(self):
        """Invoked when 'Lock' button in rma form view is clicked."""
        self.filtered("can_be_locked").write({"state": "locked"})

    def action_unlock(self):
        """Invoked when 'Unlock' button in rma form view is clicked."""
        locked_rma = self.filtered(lambda r: r.state == "locked")
        locked_rma.write({"state": "received"})

    def action_preview(self):
        """Invoked when 'Preview' button in rma form view is clicked."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "target": "self",
            "url": self.get_portal_url(),
        }

    def action_view_receipt(self):
        """Invoked when 'Receipt' smart button in rma form view is clicked."""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock.action_picking_tree_all"
        )
        action.update(
            res_id=self.reception_move_ids.picking_id.id,
            view_mode="form",
            view_id=False,
            views=False,
        )
        return action

    def action_view_refund(self):
        """Invoked when 'Refund' smart button in rma form view is clicked."""
        self.ensure_one()
        return {
            "name": _("Refund"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "account.move",
            "views": [(self.env.ref("account.view_move_form").id, "form")],
            "res_id": self.refund_id.id,
        }

    def action_view_delivery(self):
        """Invoked when 'Delivery' smart button in rma form view is clicked."""
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock.action_picking_tree_all"
        )
        picking = self.delivery_move_ids.mapped("picking_id")
        if len(picking) > 1:
            action["domain"] = [("id", "in", picking.ids)]
        elif picking:
            action.update(
                res_id=picking.id,
                view_mode="form",
                view_id=False,
                views=False,
            )
        return action

    # Validation business methods
    def _ensure_required_fields(self):
        """This method is used to ensure the following fields are not empty:
        [
            'partner_id', 'partner_invoice_id', 'partner_shipping_id',
            'product_id', 'location_id'
        ]

        This method is intended to be called on confirm RMA action and is
        invoked by:
        rma._check_required_after_draft
        rma.action_confirm
        """
        ir_translation = self.env["ir.translation"]
        required = [
            "partner_id",
            "partner_shipping_id",
            "partner_invoice_id",
            "product_id",
            "location_id",
        ]
        for record in self:
            desc = ""
            for field in filter(lambda item: not record[item], required):
                desc += "\n%s" % ir_translation.get_field_string("rma")[field]
            if desc:
                raise ValidationError(_("Required field(s):%s") % desc)

    def _ensure_can_be_returned(self):
        """This method is intended to be invoked after user click on
        'Replace' or 'Return to customer' button (before the delivery wizard
        is launched) and after confirm the wizard.

        This method is invoked by:
        rma.action_replace
        rma.action_return
        rma.create_replace
        rma.create_return
        """
        if len(self) == 1:
            if not self.can_be_returned:
                raise ValidationError(_("This RMA cannot perform a return."))
        elif not self.filtered("can_be_returned"):
            raise ValidationError(_("None of the selected RMAs can perform a return."))

    def _ensure_can_be_replaced(self):
        """This method is intended to be invoked after user click on
        'Replace' button (before the delivery wizard
        is launched) and after confirm the wizard.

        This method is invoked by:
        rma.action_replace
        rma.create_replace
        """
        if len(self) == 1:
            if not self.can_be_replaced:
                raise ValidationError(_("This RMA cannot perform a replacement."))
        elif not self.filtered("can_be_replaced"):
            raise ValidationError(
                _("None of the selected RMAs can perform a replacement.")
            )

    def _ensure_can_be_split(self):
        """intended to be called before launch and after save the split wizard.
        invoked by:
        rma.action_split
        rma.extract_quantity
        """
        self.ensure_one()
        if not self.can_be_split:
            raise ValidationError(_("This RMA cannot be split."))

    def _ensure_qty_to_return(self, qty=None, uom=None):
        """This method is intended to be invoked after confirm the wizard.
        invoked by: rma.create_return
        """
        if qty and uom:
            if uom != self.product_uom:
                qty = uom._compute_quantity(qty, self.product_uom)
            if qty > self.remaining_qty:
                raise ValidationError(
                    _("The quantity to return is greater than " "remaining quantity.")
                )

    def _ensure_qty_to_extract(self, qty, uom):
        """This method is intended to be invoked after confirm the wizard.
        invoked by: rma.extract_quantity
        """
        to_split_uom_qty = qty
        if uom != self.product_uom:
            to_split_uom_qty = uom._compute_quantity(qty, self.product_uom)
        if to_split_uom_qty > self.remaining_qty:
            raise ValidationError(
                _(
                    "Quantity to extract cannot be greater than remaining "
                    "delivery quantity (%s %s)"
                )
                % (self.remaining_qty, self.product_uom.name)
            )

    # Extract business methods
    def extract_quantity(self, qty, uom):
        self.ensure_one()
        self._ensure_can_be_split()
        self._ensure_qty_to_extract(qty, uom)
        self.product_uom_qty -= uom._compute_quantity(qty, self.product_uom)
        if self.remaining_qty_to_done <= 0:
            if self.state == "waiting_return":
                self.state = "returned"
            elif self.state == "waiting_replacement":
                self.state = "replaced"
        extracted_rma = self.copy(
            {
                "origin": self.name,
                "product_uom_qty": qty,
                "product_uom": uom.id,
                "state": "received",
                "reception_move_ids": [(6, 0, self.reception_move_ids.ids)],
                "origin_split_rma_id": self.id,
            }
        )
        extracted_rma.message_post_with_view(
            "mail.message_origin_link",
            values={"self": extracted_rma, "origin": self},
            subtype_id=self.env.ref("mail.mt_note").id,
        )
        self.message_post(
            body=_(
                'Split: <a href="#" data-oe-model="rma" '
                'data-oe-id="%d">%s</a> has been created.'
            )
            % (
                extracted_rma.id,
                extracted_rma.name,
            )
        )
        return extracted_rma

    # Refund business methods
    def _prepare_refund(self, invoice_form, origin):
        """Hook method for preparing the refund Form.

        This method could be override in order to add new custom field
        values in the refund creation.

        invoked by:
        rma.action_refund
        """
        self.ensure_one()
        invoice_form.partner_id = self.partner_invoice_id
        # Avoid set partner default value
        invoice_form.invoice_payment_term_id = self.env["account.payment.term"]

    def _prepare_refund_line(self, line_form):
        """Hook method for preparing a refund line Form.

        This method could be override in order to add new custom field
        values in the refund line creation.

        invoked by:
        rma.action_refund
        """
        self.ensure_one()
        product = self._get_refund_line_product()
        qty, uom = self._get_refund_line_quantity()
        line_form.product_id = product
        line_form.quantity = qty
        line_form.product_uom_id = uom
        line_form.price_unit = self._get_refund_line_price_unit()

    def _get_refund_line_product(self):
        """To be overriden in a third module with the proper origin values
        in case a kit is linked with the rma"""
        return self.product_id

    def _get_refund_line_quantity(self):
        """To be overriden in a third module with the proper origin values
        in case a kit is linked with the rma"""
        return (self.product_uom_qty, self.product_uom)

    def _get_refund_line_price_unit(self):
        """To be overriden in a third module with the proper origin values
        in case a sale order is linked to the original move"""
        return self.product_id.lst_price

    def _get_extra_refund_line_vals(self):
        """Override to write aditional stuff into the refund line"""
        return {}

    def _delivery_should_be_grouped(self):
        """Checks if the rmas should be grouped for the delivery process"""
        group_returns = self.env.company.rma_return_grouping
        if "rma_return_grouping" in self.env.context:
            group_returns = self.env.context.get("rma_return_grouping")
        return group_returns

    def _delivery_group_key(self):
        """Returns a key by which the rmas should be grouped for the delivery process"""
        self.ensure_one()
        return (self.partner_shipping_id.id, self.company_id.id, self.warehouse_id.id)

    def _group_delivery_if_needed(self):
        """Groups the given rmas by the returned key from _delivery_group_key
        by setting the procurement_group_id on the each rma if there is not yet on set"""
        if not self._delivery_should_be_grouped():
            return
        grouped_rmas = groupby(
            sorted(self, key=lambda rma: rma._delivery_group_key()),
            key=lambda rma: [rma._delivery_group_key()],
        )
        for _group, rmas in grouped_rmas:
            rmas = (
                self.browse()
                .concat(*list(rmas))
                .filtered(lambda rma: not rma.procurement_group_id)
            )
            if not rmas:
                continue
            proc_group = rmas._create_delivery_procurement_group()
            rmas.write({"procurement_group_id": proc_group.id})

    def _prepare_outgoing_procurement_values(self, warehouse=None, scheduled_date=None):
        values = self._prepare_procurement_values(warehouse, scheduled_date)
        values.update({"rma_id": self.id})
        return values

    def _prepare_delivery_procurement_values(self, scheduled_date=None):
        values = self._prepare_outgoing_procurement_values(
            scheduled_date=scheduled_date
        )
        values.update(
            {
                "move_orig_ids": [(6, 0, self.reception_move_ids.ids)],
            }
        )
        return values

    def _prepare_delivery_procurement(self, scheduled_date=None, qty=None, uom=None):
        self.ensure_one()
        values = self._prepare_delivery_procurement_values(scheduled_date)
        return self._prepare_procurement(
            self.partner_shipping_id.property_stock_customer,
            values,
            qty=qty,
            uom=uom,
        )

    def _prepare_delivery_procurement_group_values(self):
        return {}

    def _create_delivery_procurement_group(self):
        return self._create_procurement_group(
            self._prepare_delivery_procurement_group_values()
        )

    def _prepare_delivery_procurements(self, scheduled_date=None, qty=None, uom=None):
        self._group_delivery_if_needed()
        procurements = []
        for rma in self:
            if not rma.procurement_group_id:
                rma.procurement_group_id = rma._create_delivery_procurement_group()
            procurements.append(
                rma._prepare_delivery_procurement(scheduled_date, qty, uom)
            )
        return procurements

    def _create_delivery(self, scheduled_date=None, qty=None, uom=None):
        procurements = self._prepare_delivery_procurements(scheduled_date, qty, uom)
        self._run_procurements(procurements)

    def _post_process_create_deliveries(self):
        pickings = defaultdict(lambda: self.browse())
        for rma in self:
            # TODO: warum sind hier mehr als eins vorhanden
            _pickings = rma.delivery_move_ids.picking_id
            if not _pickings:
                continue
            picking = _pickings.sorted("id", reverse=True)[0]
            pickings[picking] |= rma
            rma.message_post(
                body=_(
                    'Return: <a href="#" data-oe-model="stock.picking" '
                    'data-oe-id="%d">%s</a> has been created.'
                )
                % (picking.id, picking.name)
            )
        for picking, rmas in pickings.items():
            picking.action_confirm()
            picking.action_assign()
            picking.message_post_with_view(
                "mail.message_origin_link",
                values={"self": picking, "origin": rmas},
                subtype_id=self.env.ref("mail.mt_note").id,
            )

    def create_deliveries(
        self, scheduled_date=None, qty=None, uom=None, set_state=True
    ):
        rmas_to_return = self.filtered(
            lambda rma: rma.can_be_returned and rma._product_is_storable()
        )
        if not rmas_to_return:
            return
        rmas_to_return._create_delivery(scheduled_date, qty, uom)
        rmas_to_return._post_process_create_deliveries()
        if set_state:
            rmas_to_return.write({"state": "waiting_return"})

    # Returning business methods
    def create_return(self, scheduled_date, qty=None, uom=None, set_state=True):
        """Intended to be invoked by the delivery wizard"""
        self._ensure_can_be_returned()
        self._ensure_qty_to_return(qty, uom)
        self.create_deliveries(scheduled_date, qty, uom, set_state)

    def _prepare_replace_procurement_values(self, warehouse=None, scheduled_date=None):
        return self._prepare_outgoing_procurement_values(warehouse, scheduled_date)

    def _prepare_replace_procurement_group_values(self):
        return {}

    def _create_replace_procurement_group(self):
        return self._create_procurement_group(
            self._prepare_replace_procurement_group_values()
        )

    def _prepare_replace_procurement(
        self, warehouse, scheduled_date, product, qty, uom
    ):
        if not self.procurement_group_id:
            self.procurement_group_id = self._create_replace_procurement_group()

        values = self._prepare_replace_procurement_values(warehouse, scheduled_date)
        return self._prepare_procurement(
            self.partner_shipping_id.property_stock_customer,
            values,
            product,
            qty,
            uom,
        )

    def _prepare_replace_procurements(
        self, warehouse, scheduled_date, product, qty, uom
    ):
        procurements = []
        for rma in self:
            if not rma._product_is_storable(product):
                continue

            procurements.append(
                rma._prepare_replace_procurement(
                    warehouse, scheduled_date, product, qty, uom
                )
            )
        return procurements

    def _create_replace(self, warehouse, scheduled_date, product, qty, uom):
        procurements = self._prepare_replace_procurements(
            warehouse, scheduled_date, product, qty, uom
        )
        self.env["procurement.group"].run(procurements)

    # Replacing business methods
    def create_replace(self, scheduled_date, warehouse, product, qty, uom):
        """Intended to be invoked by the delivery wizard"""
        self._ensure_can_be_replaced()
        moves_before = self.delivery_move_ids
        self._create_replace(warehouse, scheduled_date, product, qty, uom)
        new_moves = self.delivery_move_ids - moves_before
        body = ""
        # The product replacement could explode into several moves like in the case of
        # MRP BoM Kits
        for new_move in new_moves:
            body += (
                _(
                    "Replacement: "
                    'Move <a href="#" data-oe-model="stock.move" '
                    'data-oe-id="%d">%s</a> (Picking <a href="#" '
                    'data-oe-model="stock.picking" data-oe-id="%d">%s</a>) '
                    "has been created."
                )
                % (
                    new_move.id,
                    new_move.name_get()[0][1],
                    new_move.picking_id.id,
                    new_move.picking_id.name,
                )
                + "\n"
            )
        for rma in self:
            rma.message_post(
                body=body
                or _(
                    "Replacement:<br/>"
                    'Product <a href="#" data-oe-model="product.product" '
                    'data-oe-id="%d">%s</a><br/>'
                    "Quantity %f %s<br/>"
                    "This replacement did not create a new move, but one of "
                    "the previously created moves was updated with this data."
                )
                % (product.id, product.display_name, qty, uom.name)
            )
        self.write({"state": "waiting_replacement"})

    # Mail business methods
    def _creation_subtype(self):
        if self.state in ("draft"):
            return self.env.ref("rma.mt_rma_draft")
        else:
            return super()._creation_subtype()

    def _track_subtype(self, init_values):
        self.ensure_one()
        if "state" in init_values:
            if self.state == "draft":
                return self.env.ref("rma.mt_rma_draft")
            elif self.state == "confirmed":
                return self.env.ref("rma.mt_rma_notification")
        return super()._track_subtype(init_values)

    def message_new(self, msg_dict, custom_values=None):
        """Extract the needed values from an incoming rma emails data-set
        to be used to create an RMA.
        """
        if custom_values is None:
            custom_values = {}
        subject = msg_dict.get("subject", "")
        body = html2plaintext(msg_dict.get("body", ""))
        desc = _("<b>E-mail subject:</b> %s<br/><br/><b>E-mail body:</b><br/>%s") % (
            subject,
            body,
        )
        defaults = {
            "description": desc,
            "name": _("New"),
            "origin": _("Incoming e-mail"),
        }
        if msg_dict.get("author_id"):
            partner = self.env["res.partner"].browse(msg_dict.get("author_id"))
            defaults.update(
                partner_id=partner.id,
                partner_invoice_id=partner.address_get(["invoice"]).get(
                    "invoice", False
                ),
            )
        if msg_dict.get("priority"):
            defaults["priority"] = msg_dict.get("priority")
        defaults.update(custom_values)
        rma = super().message_new(msg_dict, custom_values=defaults)
        if rma.user_id and rma.user_id.partner_id not in rma.message_partner_ids:
            rma.message_subscribe([rma.user_id.partner_id.id])
        return rma

    @api.returns("mail.message", lambda value: value.id)
    def message_post(self, **kwargs):
        """Set 'sent' field to True when an email is sent from rma form
        view. This field (sent) is used to set the appropriate style to the
        'Send by Email' button in the rma form view.
        """
        if self.env.context.get("mark_rma_as_sent"):
            self.write({"sent": True})
        # mail_post_autofollow=True to include email recipient contacts as
        # RMA followers
        self_with_context = self.with_context(mail_post_autofollow=True)
        return super(Rma, self_with_context).message_post(**kwargs)

    def _message_get_suggested_recipients(self):
        recipients = super()._message_get_suggested_recipients()
        try:
            for record in self.filtered("partner_id"):
                record._message_add_suggested_recipient(
                    recipients, partner=record.partner_id, reason=_("Customer")
                )
        except AccessError:  # no read access rights
            pass
        return recipients

    # Reporting business methods
    def _get_report_base_filename(self):
        self.ensure_one()
        return "RMA Report - %s" % self.name

    # Other business methods

    def update_received_state_on_reception(self):
        """Invoked by:
        [stock.move]._action_done
        Here we can attach methods to trigger when the customer products
        are received on the RMA location, such as automatic notifications
        """
        self.write({"state": "received"})
        self._send_receipt_confirmation_email()

    def update_received_state(self):
        """Invoked by:
        [stock.move].unlink
        [stock.move]._action_cancel
        """
        rma = self.filtered(lambda r: r.delivered_qty == 0)
        if rma:
            rma.write({"state": "received"})

    def update_replaced_state(self):
        """Invoked by:
        [stock.move]._action_done
        [stock.move].unlink
        [stock.move]._action_cancel
        """
        rma = self.filtered(
            lambda r: (
                r.state == "waiting_replacement"
                and 0 >= r.remaining_qty_to_done == r.remaining_qty
            )
        )
        if rma:
            rma.write({"state": "replaced"})

    def update_returned_state(self):
        """Invoked by [stock.move]._action_done"""
        rma = self.filtered(
            lambda r: (r.state == "waiting_return" and r.remaining_qty_to_done <= 0)
        )
        if rma:
            rma.write({"state": "returned"})
