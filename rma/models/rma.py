# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form
from odoo.tools import html2plaintext
import odoo.addons.decimal_precision as dp
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from collections import Counter


class Rma(models.Model):
    _name = "rma"
    _description = "RMA"
    _order = "date desc, priority"
    _inherit = ["mail.thread", "portal.mixin", "mail.activity.mixin"]

    def _domain_location_id(self):
        rma_loc = self.env['stock.warehouse'].search([]).mapped('rma_loc_id')
        return [('id', 'child_of', rma_loc.ids)]

    # General fields
    sent = fields.Boolean()
    name = fields.Char(
        string='Name',
        index=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
        default=lambda self: _('New'),
    )
    origin = fields.Char(
        string='Source Document',
        states={
            'locked': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
        help="Reference of the document that generated this RMA.",
    )
    date = fields.Datetime(
        default=lambda self: fields.Datetime.now(),
        index=True,
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    deadline = fields.Date(
        states={
            'locked': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Responsible",
        track_visibility="always",
        states={
            'locked': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
    )
    team_id = fields.Many2one(
        comodel_name="rma.team",
        string="RMA team",
        index=True,
        states={
            'locked': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.user.company_id,
        states={
            'locked': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
    )
    partner_id = fields.Many2one(
        string="Customer",
        comodel_name="res.partner",
        readonly=True,
        states={'draft': [('readonly', False)]},
        index=True,
        track_visibility='always'
    )
    partner_shipping_id = fields.Many2one(
        string="Shipping Address",
        comodel_name="res.partner",
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Shipping address for current RMA."
    )
    partner_invoice_id = fields.Many2one(
        string="Invoice Address",
        comodel_name="res.partner",
        readonly=True,
        states={'draft': [('readonly', False)]},
        domain=[('customer', '=', True)],
        help="Refund address for current RMA."
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
        states={'draft': [('readonly', False)]},
    )
    move_id = fields.Many2one(
        comodel_name='stock.move',
        string='Origin move',
        domain="["
               "    ('picking_id', '=', picking_id),"
               "    ('picking_id', '!=', False)"
               "]",
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        domain=[('type', 'in', ['consu', 'product'])],
    )
    product_uom_qty = fields.Float(
        string="Quantity",
        required=True,
        default=1.0,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    product_uom = fields.Many2one(
        comodel_name="uom.uom",
        string="UoM",
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env.ref('uom.product_uom_unit').id,
    )
    procurement_group_id = fields.Many2one(
        comodel_name='procurement.group',
        string='Procurement group',
        readonly=True,
        states={
            'draft': [('readonly', False)],
            'confirmed': [('readonly', False)],
            'received': [('readonly', False)],
        },
    )
    priority = fields.Selection(
        string="Priority",
        selection=PROCUREMENT_PRIORITIES,
        default="1",
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    operation_id = fields.Many2one(
        comodel_name='rma.operation',
        string='Requested operation',
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
            ("locked", "Locked"),
            ("cancelled", "Canceled"),
        ],
        default="draft",
        copy=False,
        track_visibility="onchange",
    )
    description = fields.Html(
        states={
            'locked': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
    )
    # Reception fields
    location_id = fields.Many2one(
        comodel_name='stock.location',
        domain=_domain_location_id,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        compute="_compute_warehouse_id",
        store=True,
    )
    reception_move_id = fields.Many2one(
        comodel_name='stock.move',
        string='Reception move',
        copy=False,
    )
    # Refund fields
    refund_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Refund',
        readonly=True,
        copy=False,
    )
    refund_line_id = fields.Many2one(
        comodel_name='account.invoice.line',
        string='Refund line',
        readonly=True,
        copy=False,
    )
    can_be_refunded = fields.Boolean(
        compute="_compute_can_be_refunded"
    )
    # Delivery fields
    delivery_move_ids = fields.One2many(
        comodel_name='stock.move',
        inverse_name='rma_id',
        string='Delivery reservation',
        readonly=True,
        copy=False,
    )
    delivery_picking_count = fields.Integer(
        string='Delivery count',
        compute='_compute_delivery_picking_count',
    )
    delivered_qty = fields.Float(
        string="Delivered qty",
        digits=dp.get_precision('Product Unit of Measure'),
        compute='_compute_delivered_qty',
        store=True,
    )
    delivered_qty_done = fields.Float(
        string="Delivered qty done",
        digits=dp.get_precision('Product Unit of Measure'),
        compute='_compute_delivered_qty',
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
    remaining_qty = fields.Float(
        string="Remaining delivered qty",
        digits=dp.get_precision('Product Unit of Measure'),
        compute='_compute_remaining_qty',
    )
    remaining_qty_to_done = fields.Float(
        string="Remaining delivered qty to done",
        digits=dp.get_precision('Product Unit of Measure'),
        compute='_compute_remaining_qty',
    )
    # Split fields
    can_be_split = fields.Boolean(
        compute="_compute_can_be_split",
    )
    origin_split_rma_id = fields.Many2one(
        comodel_name='rma',
        string='Extracted from',
        readonly=True,
        copy=False,
    )

    def _compute_delivery_picking_count(self):
        # It is enough to count the moves to know how many pickings
        # there are because there will be a unique move linked to the
        # same picking and the same rma.
        rma_data = self.env['stock.move'].read_group(
            [('rma_id', 'in', self.ids)],
            ['rma_id', 'picking_id'],
            ['rma_id', 'picking_id'],
            lazy=False,
        )
        mapped_data = Counter(map(lambda r: r['rma_id'][0], rma_data))
        for record in self:
            record.delivery_picking_count = mapped_data.get(record.id, 0)

    @api.depends(
        'delivery_move_ids',
        'delivery_move_ids.state',
        'delivery_move_ids.scrapped',
        'delivery_move_ids.product_uom_qty',
        'delivery_move_ids.reserved_availability',
        'delivery_move_ids.quantity_done',
        'delivery_move_ids.product_uom',
        'product_uom',
    )
    def _compute_delivered_qty(self):
        """ Compute 'delivered_qty' and 'delivered_qty_done' fields.

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
                    lambda r: r.state != 'cancel' and not r.scrapped):
                if move.quantity_done:
                    quantity_done = move.product_uom._compute_quantity(
                        move.quantity_done, record.product_uom)
                    if move.state == 'done':
                        delivered_qty_done += quantity_done
                    delivered_qty += quantity_done
                elif move.reserved_availability:
                    delivered_qty += move.product_uom._compute_quantity(
                        move.reserved_availability, record.product_uom)
                elif move.product_uom_qty:
                    delivered_qty += move.product_uom._compute_quantity(
                        move.product_uom_qty, record.product_uom)
            record.delivered_qty = delivered_qty
            record.delivered_qty_done = delivered_qty_done

    @api.depends('product_uom_qty', 'delivered_qty', 'delivered_qty_done')
    def _compute_remaining_qty(self):
        """ Compute 'remaining_qty' and 'remaining_qty_to_done' fields.

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
        'state',
    )
    def _compute_can_be_refunded(self):
        """ Compute 'can_be_refunded'. This field controls the visibility
        of 'Refund' button in the rma form view and determinates if
        an rma can be refunded. It is used in rma.action_refund method.
        """
        for record in self:
            record.can_be_refunded = record.state == 'received'

    @api.depends('remaining_qty', 'state')
    def _compute_can_be_returned(self):
        """ Compute 'can_be_returned'. This field controls the visibility
        of the 'Return to customer' button in the rma form
        view and determinates if an rma can be returned to the customer.
        This field is used in:
        rma._compute_can_be_split
        rma._ensure_can_be_returned.
        """
        for r in self:
            r.can_be_returned = (r.state in ['received', 'waiting_return']
                                 and r.remaining_qty > 0)

    @api.depends('state')
    def _compute_can_be_replaced(self):
        """ Compute 'can_be_replaced'. This field controls the visibility
        of 'Replace' button in the rma form
        view and determinates if an rma can be replaced.
        This field is used in:
        rma._compute_can_be_split
        rma._ensure_can_be_replaced.
        """
        for r in self:
            r.can_be_replaced = r.state in ['received', 'waiting_replacement',
                                            'replaced']

    @api.depends('product_uom_qty', 'state', 'remaining_qty',
                 'remaining_qty_to_done')
    def _compute_can_be_split(self):
        """ Compute 'can_be_split'. This field controls the
        visibility of 'Split' button in the rma form view and
        determinates if an rma can be split.
        This field is used in:
        rma._ensure_can_be_split
        """
        for r in self:
            if (r.product_uom_qty > 1
                and ((r.state == 'waiting_return' and r.remaining_qty > 0)
                     or (r.state == 'waiting_replacement'
                         and r.remaining_qty_to_done > 0))):
                r.can_be_split = True
            else:
                r.can_be_split = False

    @api.depends('remaining_qty_to_done', 'state')
    def _compute_can_be_locked(self):
        for r in self:
            r.can_be_locked = (r.remaining_qty_to_done > 0
                               and r.state in ['received',
                                               'waiting_return',
                                               'waiting_replacement'])

    @api.depends('location_id')
    def _compute_warehouse_id(self):
        for record in self.filtered('location_id'):
            record.warehouse_id = self.env['stock.warehouse'].search(
                [('rma_loc_id', 'parent_of', record.location_id.id)], limit=1)

    def _compute_access_url(self):
        for record in self:
            record.access_url = '/my/rmas/{}'.format(record.id)

    # Constrains methods (@api.constrains)
    @api.constrains(
        'state', 'partner_id', 'partner_invoice_id',
        'partner_shipping_id', 'product_id')
    def _check_required_after_draft(self):
        """ Check that RMAs are being created or edited with the
        necessary fields filled out. Only applies to 'Draft' and
        'Cancelled' states.
        """
        rma = self.filtered(lambda r: r.state not in ['draft', 'cancelled'])
        rma._ensure_required_fields()

    # onchange methods (@api.onchange)
    @api.onchange("user_id")
    def _onchange_user_id(self):
        if self.user_id:
            self.team_id = self.env['rma.team'].sudo().search([
                '|',
                ('user_id', '=', self.user_id.id),
                ('member_ids', '=', self.user_id.id),
                '|',
                ('company_id', '=', False),
                ('company_id', 'child_of', self.company_id.ids)
            ], limit=1)
        else:
            self.team_id = False

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        self.picking_id = False
        partner_invoice_id = False
        partner_shipping_id = False
        if self.partner_id:
            address = self.partner_id.address_get(['invoice', 'delivery'])
            partner_invoice_id = address.get('invoice', False)
            partner_shipping_id = address.get('delivery', False)
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
        domain_product_uom = []
        if self.product_id:
            # Set UoM and UoM domain (product_uom)
            domain_product_uom = [
                ('category_id', '=', self.product_id.uom_id.category_id.id)
            ]
            if (not self.product_uom
                    or self.product_id.uom_id.id != self.product_uom.id):
                self.product_uom = self.product_id.uom_id
            # Set stock location (location_id)
            user = self.env.user
            if (not user.has_group('stock.group_stock_multi_locations')
                    and not self.location_id):
                # If this condition is True, it is because a picking is not set
                company = self.company_id or self.env.user.company_id
                warehouse = self.env['stock.warehouse'].search(
                    [('company_id', '=', company.id)], limit=1)
                self.location_id = warehouse.rma_loc_id.id
        return {'domain': {'product_uom': domain_product_uom}}

    # CRUD methods (ORM overrides)
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            ir_sequence = self.env['ir.sequence']
            if 'company_id' in vals:
                ir_sequence = ir_sequence.with_context(
                    force_company=vals['company_id'])
            vals['name'] = ir_sequence.next_by_code('rma')
        # Assign a default team_id which will be the first in the sequence
        if "team_id" not in vals:
            vals["team_id"] = self.env["rma.team"].search([], limit=1).id
        return super().create(vals)

    @api.multi
    def copy(self, default=None):
        team = super().copy(default)
        for follower in self.message_follower_ids:
            team.message_subscribe(partner_ids=follower.partner_id.ids,
                                   subtype_ids=follower.subtype_ids.ids)
        return team

    def unlink(self):
        if self.filtered(lambda r: r.state != 'draft'):
            raise ValidationError(
                _("You cannot delete RMAs that are not in draft state"))
        return super().unlink()

    def _send_confirmation_email(self):
        """Auto send notifications"""
        for rma in self.filtered(lambda p: p.company_id.send_rma_confirmation):
            rma_template_id = (
                rma.company_id.rma_mail_confirmation_template_id.id
            )
            rma.with_context(
                force_send=True,
                mark_rma_as_sent=True
            ).message_post_with_template(rma_template_id)

    # Action methods
    def action_rma_send(self):
        self.ensure_one()
        template = self.env.ref('rma.mail_template_rma_notification', False)
        template = (
            self.company_id.rma_mail_confirmation_template_id or template)
        form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = {
            'default_model': 'rma',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template),
            'default_template_id': template and template.id or False,
            'default_composition_mode': 'comment',
            'mark_rma_as_sent': True,
            'model_description': 'RMA',
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(form.id, 'form')],
            'view_id': form.id,
            'target': 'new',
            'context': ctx,
        }

    def action_confirm(self):
        """Invoked when 'Confirm' button in rma form view is clicked."""
        self.ensure_one()
        self._ensure_required_fields()
        if self.state == 'draft':
            if self.picking_id:
                reception_move = self._create_receptions_from_picking()
            else:
                reception_move = self._create_receptions_from_product()
            self.write({
                'reception_move_id': reception_move.id,
                'state': 'confirmed',
            })
            if self.partner_id not in self.message_partner_ids:
                self.message_subscribe([self.partner_id.id])
            self._send_confirmation_email()

    def action_refund(self):
        """Invoked when 'Refund' button in rma form view is clicked
        and 'rma_refund_action_server' server action is run.
        """
        group_dict = {}
        for record in self.filtered("can_be_refunded"):
            key = (record.partner_invoice_id.id, record.company_id.id)
            group_dict.setdefault(key, self.env['rma'])
            group_dict[key] |= record
        for rmas in group_dict.values():
            origin = ', '.join(rmas.mapped('name'))
            invoice_form = Form(self.env['account.invoice'].with_context(
                default_type='out_refund',
                company_id=rmas[0].company_id.id,
            ), "account.invoice_form")
            rmas[0]._prepare_refund(invoice_form, origin)
            refund = invoice_form.save()
            for rma in rmas:
                with invoice_form.invoice_line_ids.new() as line_form:
                    rma._prepare_refund_line(line_form)
                # rma_id is not present in the form view, so we need to get
                # the 'values to save' to add the rma id and use the
                # create method instead of save the form. We also need
                # the new refund line id to be linked to the rma.
                refund_vals = invoice_form._values_to_save(all_fields=True)
                line_vals = refund_vals['invoice_line_ids'][-1][2]
                line_vals.update(invoice_id=refund.id, rma_id=rma.id)
                line = self.env['account.invoice.line'].create(line_vals)
                rma.write({
                    'refund_line_id': line.id,
                    'refund_id': refund.id,
                    'state': 'refunded',
                })
            refund.message_post_with_view(
                'mail.message_origin_link',
                values={'self': refund, 'origin': rmas},
                subtype_id=self.env.ref('mail.mt_note').id,
            )

    def action_replace(self):
        """Invoked when 'Replace' button in rma form view is clicked."""
        self.ensure_one()
        self._ensure_can_be_replaced()
        # Force active_id to avoid issues when coming from smart buttons
        # in other models
        action = self.env.ref("rma.rma_delivery_wizard_action").with_context(
            active_id=self.id).read()[0]
        action['name'] = 'Replace product(s)'
        action['context'] = dict(self.env.context)
        action['context'].update(
            active_id=self.id,
            active_ids=self.ids,
            rma_delivery_type='replace',
        )
        return action

    def action_return(self):
        """Invoked when 'Return to customer' button in rma form
        view is clicked.
        """
        self.ensure_one()
        self._ensure_can_be_returned()
        # Force active_id to avoid issues when coming from smart buttons
        # in other models
        action = self.env.ref("rma.rma_delivery_wizard_action").with_context(
            active_id=self.id).read()[0]
        action['context'] = dict(self.env.context)
        action['context'].update(
            active_id=self.id,
            active_ids=self.ids,
            rma_delivery_type='return',
        )
        return action

    def action_split(self):
        """Invoked when 'Split' button in rma form view is clicked."""
        self.ensure_one()
        self._ensure_can_be_split()
        # Force active_id to avoid issues when coming from smart buttons
        # in other models
        action = self.env.ref("rma.rma_split_wizard_action").with_context(
            active_id=self.id).read()[0]
        action['context'] = dict(self.env.context)
        action['context'].update(active_id=self.id, active_ids=self.ids)
        return action

    def action_cancel(self):
        """Invoked when 'Cancel' button in rma form view is clicked."""
        self.mapped('reception_move_id')._action_cancel()
        self.write({'state': 'cancelled'})

    def action_draft(self):
        cancelled_rma = self.filtered(lambda r: r.state == 'cancelled')
        cancelled_rma.write({'state': 'draft'})

    def action_lock(self):
        """Invoked when 'Lock' button in rma form view is clicked."""
        self.filtered("can_be_locked").write({'state': 'locked'})

    def action_unlock(self):
        """Invoked when 'Unlock' button in rma form view is clicked."""
        locked_rma = self.filtered(lambda r: r.state == 'locked')
        locked_rma.write({'state': 'received'})

    def action_preview(self):
        """Invoked when 'Preview' button in rma form view is clicked."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }

    def action_view_receipt(self):
        """Invoked when 'Receipt' smart button in rma form view is clicked."""
        self.ensure_one()
        # Force active_id to avoid issues when coming from smart buttons
        # in other models
        action = self.env.ref('stock.action_picking_tree_all').with_context(
            active_id=self.id).read()[0]
        action.update(
            res_id=self.reception_move_id.picking_id.id,
            view_mode="form",
            view_id=False,
            views=False,
        )
        return action

    def action_view_refund(self):
        """Invoked when 'Refund' smart button in rma form view is clicked."""
        self.ensure_one()
        return {
            'name': _('Refund'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'views': [(self.env.ref('account.invoice_form').id, 'form')],
            'res_id': self.refund_id.id,
        }

    def action_view_delivery(self):
        """Invoked when 'Delivery' smart button in rma form view is clicked."""
        action = self.env.ref('stock.action_picking_tree_all').with_context(
            active_id=self.id).read()[0]
        picking = self.delivery_move_ids.mapped('picking_id')
        if len(picking) > 1:
            action['domain'] = [('id', 'in', picking.ids)]
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
        """ This method is used to ensure the following fields are not empty:
        [
            'partner_id', 'partner_invoice_id', 'partner_shipping_id',
            'product_id', 'location_id'
        ]

        This method is intended to be called on confirm RMA action and is
        invoked by:
        rma._check_required_after_draft
        rma.action_confirm
        """
        ir_translation = self.env['ir.translation']
        required = [
            'partner_id', 'partner_invoice_id', 'partner_shipping_id',
            'product_id', 'location_id'
        ]
        for record in self:
            desc = ""
            for field in filter(lambda item: not record[item], required):
                desc += "\n%s" % ir_translation.get_field_string("rma")[field]
            if desc:
                raise ValidationError(_('Required field(s):%s') % desc)

    def _ensure_can_be_returned(self):
        """ This method is intended to be invoked after user click on
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
                raise ValidationError(
                    _("This RMA cannot perform a return."))
        elif not self.filtered("can_be_returned"):
            raise ValidationError(
                _("None of the selected RMAs can perform a return."))

    def _ensure_can_be_replaced(self):
        """ This method is intended to be invoked after user click on
        'Replace' button (before the delivery wizard
        is launched) and after confirm the wizard.

        This method is invoked by:
        rma.action_replace
        rma.create_replace
        """
        if len(self) == 1:
            if not self.can_be_replaced:
                raise ValidationError(
                    _("This RMA cannot perform a replacement."))
        elif not self.filtered("can_be_replaced"):
            raise ValidationError(
                _("None of the selected RMAs can perform a replacement."))

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
        """ This method is intended to be invoked after confirm the wizard.
        invoked by: rma.create_return
        """
        if qty and uom:
            if uom != self.product_uom:
                qty = uom._compute_quantity(qty, self.product_uom)
            if qty > self.remaining_qty:
                raise ValidationError(
                    _("The quantity to return is greater than "
                      "remaining quantity."))

    def _ensure_qty_to_extract(self, qty, uom):
        """ This method is intended to be invoked after confirm the wizard.
        invoked by: rma.extract_quantity
        """
        to_split_uom_qty = qty
        if uom != self.product_uom:
            to_split_uom_qty = uom._compute_quantity(qty, self.product_uom)
        if to_split_uom_qty > self.remaining_qty:
            raise ValidationError(
                _("Quantity to extract cannot be greater than remaining "
                  "delivery quantity (%s %s)")
                % (self.remaining_qty, self.product_uom.name)
            )

    # Reception business methods
    def _create_receptions_from_picking(self):
        self.ensure_one()
        create_vals = {}
        if self.location_id:
            create_vals['location_id'] = self.location_id.id
        return_wizard = self.env['stock.return.picking'].with_context(
            active_id=self.picking_id.id,
            active_ids=self.picking_id.ids,
        ).create(create_vals)
        return_wizard.product_return_moves.filtered(
            lambda r: r.move_id != self.move_id
        ).unlink()
        return_line = return_wizard.product_return_moves
        return_line.quantity = self.product_uom_qty
        # set_rma_picking_type is to override the copy() method of stock
        # picking and change the default picking type to rma picking type.
        picking_action = return_wizard.with_context(
            set_rma_picking_type=True).create_returns()
        picking_id = picking_action['res_id']
        picking = self.env['stock.picking'].browse(picking_id)
        picking.origin = "%s (%s)" % (self.name, picking.origin)
        move = picking.move_lines
        move.priority = self.priority
        return move

    def _create_receptions_from_product(self):
        self.ensure_one()
        picking_form = Form(
            recordp=self.env['stock.picking'].with_context(
                default_picking_type_id=self.warehouse_id.rma_in_type_id.id),
            view="stock.view_picking_form",
        )
        self._prepare_picking(picking_form)
        picking = picking_form.save()
        picking.action_confirm()
        picking.action_assign()
        picking.message_post_with_view(
            'mail.message_origin_link',
            values={'self': picking, 'origin': self},
            subtype_id=self.env.ref('mail.mt_note').id,
        )
        return picking.move_lines

    def _prepare_picking(self, picking_form):
        picking_form.company_id = self.company_id
        picking_form.origin = self.name
        picking_form.partner_id = self.partner_shipping_id
        picking_form.location_dest_id = self.location_id
        with picking_form.move_ids_without_package.new() as move_form:
            move_form.product_id = self.product_id
            move_form.product_uom_qty = self.product_uom_qty
            move_form.product_uom = self.product_uom

    # Extract business methods
    def extract_quantity(self, qty, uom):
        self.ensure_one()
        self._ensure_can_be_split()
        self._ensure_qty_to_extract(qty, uom)
        self.product_uom_qty -= uom._compute_quantity(qty, self.product_uom)
        if self.remaining_qty_to_done <= 0:
            if self.state == 'waiting_return':
                self.state = 'returned'
            elif self.state == 'waiting_replacement':
                self.state = 'replaced'
        extracted_rma = self.copy({
            'origin': self.name,
            'product_uom_qty': qty,
            'product_uom': uom.id,
            'state': 'received',
            'reception_move_id': self.reception_move_id.id,
            'origin_split_rma_id': self.id,
        })
        extracted_rma.message_post_with_view(
            'mail.message_origin_link',
            values={'self': extracted_rma, 'origin': self},
            subtype_id=self.env.ref('mail.mt_note').id,
        )
        self.message_post(
            body=_(
                'Split: <a href="#" data-oe-model="rma" '
                'data-oe-id="%d">%s</a> has been created.'
            ) % (
                extracted_rma.id,
                extracted_rma.name,
            )
        )
        return extracted_rma

    # Refund business methods
    def _prepare_refund(self, invoice_form, origin):
        """ Hook method for preparing the refund Form.

        This method could be override in order to add new custom field
        values in the refund creation.

        invoked by:
        rma.action_refund
        """
        self.ensure_one()
        invoice_form.company_id = self.company_id
        invoice_form.partner_id = self.partner_invoice_id
        invoice_form.origin = origin

    def _prepare_refund_line(self, line_form):
        """ Hook method for preparing a refund line Form.

        This method could be override in order to add new custom field
        values in the refund line creation.

        invoked by:
        rma.action_refund
        """
        self.ensure_one()
        line_form.product_id = self.product_id
        line_form.quantity = self.product_uom_qty
        line_form.uom_id = self.product_uom
        line_form.price_unit = self._get_refund_line_price_unit()

    def _get_refund_line_price_unit(self):
        """To be overriden in a third module with the proper origin values
        in case a sale order is linked to the original move"""
        return self.product_id.lst_price

    # Returning business methods
    def create_return(self, scheduled_date, qty=None, uom=None):
        """Intended to be invoked by the delivery wizard"""
        self._ensure_can_be_returned()
        self._ensure_qty_to_return(qty, uom)
        group_dict = {}
        for record in self.filtered('can_be_returned'):
            key = (record.partner_shipping_id.id, record.company_id.id,
                   record.warehouse_id)
            group_dict.setdefault(key, self.env['rma'])
            group_dict[key] |= record
        for rmas in group_dict.values():
            origin = ', '.join(rmas.mapped('name'))
            rma_out_type = rmas[0].warehouse_id.rma_out_type_id
            picking_form = Form(
                recordp=self.env['stock.picking'].with_context(
                    default_picking_type_id=rma_out_type.id),
                view="stock.view_picking_form",
            )
            rmas[0]._prepare_returning_picking(picking_form, origin)
            picking = picking_form.save()
            for rma in rmas:
                with picking_form.move_ids_without_package.new() as move_form:
                    rma._prepare_returning_move(
                        move_form, scheduled_date, qty, uom)
                # rma_id is not present in the form view, so we need to get
                # the 'values to save' to add the rma id and use the
                # create method intead of save the form.
                picking_vals = picking_form._values_to_save(all_fields=True)
                move_vals = picking_vals['move_ids_without_package'][-1][2]
                move_vals.update(
                    picking_id=picking.id,
                    rma_id=rma.id,
                    move_orig_ids=[(4, rma.reception_move_id.id)],
                    company_id=picking.company_id.id,
                )
                self.env['stock.move'].sudo().create(move_vals)
                rma.message_post(
                    body=_(
                        'Return: <a href="#" data-oe-model="stock.picking" '
                        'data-oe-id="%d">%s</a> has been created.'
                    ) % (picking.id, picking.name)
                )
            picking.action_confirm()
            picking.action_assign()
            picking.message_post_with_view(
                'mail.message_origin_link',
                values={'self': picking, 'origin': rmas},
                subtype_id=self.env.ref('mail.mt_note').id,
            )
        self.write({'state': 'waiting_return'})

    def _prepare_returning_picking(self, picking_form, origin=None):
        picking_form.picking_type_id = self.warehouse_id.rma_out_type_id
        picking_form.company_id = self.company_id
        picking_form.origin = origin or self.name
        picking_form.partner_id = self.partner_shipping_id

    def _prepare_returning_move(self, move_form, scheduled_date,
                                quantity=None, uom=None):
        move_form.product_id = self.product_id
        move_form.product_uom_qty = quantity or self.product_uom_qty
        move_form.product_uom = uom or self.product_uom
        move_form.date_expected = scheduled_date

    # Replacing business methods
    def create_replace(self, scheduled_date, warehouse, product, qty, uom):
        """Intended to be invoked by the delivery wizard"""
        self.ensure_one()
        self._ensure_can_be_replaced()
        moves_before = self.delivery_move_ids
        self._action_launch_stock_rule(scheduled_date, warehouse, product,
                                       qty, uom)
        new_move = self.delivery_move_ids - moves_before
        if new_move:
            self.reception_move_id.move_dest_ids = [(4, new_move.id)]
            self.message_post(
                body=_(
                    'Replacement: '
                    'Move <a href="#" data-oe-model="stock.move" '
                    'data-oe-id="%d">%s</a> (Picking <a href="#" '
                    'data-oe-model="stock.picking" data-oe-id="%d">%s</a>) '
                    'has been created.'
                ) % (new_move.id, new_move.name_get()[0][1],
                     new_move.picking_id.id, new_move.picking_id.name)
            )
        else:
            self.message_post(
                body=_(
                    'Replacement:<br/>'
                    'Product <a href="#" data-oe-model="product.product" '
                    'data-oe-id="%d">%s</a><br/>'
                    'Quantity %f %s<br/>'
                    'This replacement did not create a new move, but one of '
                    'the previously created moves was updated with this data.'
                ) % (product.id, product.display_name, qty, uom.name)
            )
        if self.state != 'waiting_replacement':
            self.state = 'waiting_replacement'

    def _action_launch_stock_rule(
        self,
        scheduled_date,
        warehouse,
        product,
        qty,
        uom,
    ):
        """ Creates a delivery picking and launch stock rule. It is invoked by:
        rma.create_replace
        """
        self.ensure_one()
        if self.product_id.type not in ('consu', 'product'):
            return
        if not self.procurement_group_id:
            self.procurement_group_id = self.env['procurement.group'].create({
                'name': self.name,
                'move_type': 'direct',
                'partner_id': self.partner_shipping_id.id,
            }).id
        values = self._prepare_procurement_values(
            self.procurement_group_id, scheduled_date, warehouse)
        self.env['procurement.group'].run(
            product,
            qty,
            uom,
            self.partner_shipping_id.property_stock_customer,
            self.product_id.display_name,
            self.procurement_group_id.name,
            values,
        )

    def _prepare_procurement_values(
        self,
        group_id,
        scheduled_date,
        warehouse,
    ):
        self.ensure_one()
        return {
            'company_id': self.company_id,
            'group_id': group_id,
            'date_planned': scheduled_date,
            'warehouse_id': warehouse,
            'partner_id': self.partner_shipping_id.id,
            'rma_id': self.id,
            'priority': self.priority,
        }

    # Mail business methods
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'draft':
            return 'rma.mt_rma_draft'
        return super()._track_subtype(init_values)

    def message_new(self, msg_dict, custom_values=None):
        """Extract the needed values from an incoming rma emails data-set
        to be used to create an RMA.
        """
        if custom_values is None:
            custom_values = {}
        subject = msg_dict.get('subject', '')
        body = html2plaintext(msg_dict.get('body', ''))
        desc = _("E-mail subject: %s\n\nE-mail body:\n%s") % (subject, body)
        defaults = {
            'description': desc,
            'name': _('New'),
            'origin': _('Incoming e-mail'),
        }
        if msg_dict.get('author_id'):
            partner = self.env['res.partner'].browse(msg_dict.get('author_id'))
            defaults.update(
                partner_id=partner.id,
                partner_invoice_id=partner.address_get(
                    ['invoice']).get('invoice', False),
            )
        if msg_dict.get("priority"):
            defaults["priority"] = msg_dict.get("priority")
        defaults.update(custom_values)
        rma = super().message_new(msg_dict, custom_values=defaults)
        if (rma.user_id
                and rma.user_id.partner_id not in rma.message_partner_ids):
            rma.message_subscribe([rma.user_id.partner_id.id])
        return rma

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        """ Set 'sent' field to True when an email is sent from rma form
        view. This field (sent) is used to set the appropriate style to the
        'Send by Email' button in the rma form view.
        """
        if self.env.context.get('mark_rma_as_sent'):
            self.write({'sent': True})
        # mail_post_autofollow=True to include email recipient contacts as
        # RMA followers
        self_with_context = self.with_context(mail_post_autofollow=True)
        return super(Rma, self_with_context).message_post(**kwargs)

    @api.multi
    def message_get_suggested_recipients(self):
        recipients = super().message_get_suggested_recipients()
        try:
            for record in self.filtered("partner_id"):
                record._message_add_suggested_recipient(
                    recipients, partner=record.partner_id, reason=_('Customer'))
        except AccessError:  # no read access rights
            pass
        return recipients

    # Reporting business methods
    def _get_report_base_filename(self):
        self.ensure_one()
        return 'RMA Report - %s' % self.name

    # Other business methods
    def update_received_state(self):
        """ Invoked by:
         [stock.move].unlink
         [stock.move]._action_cancel
         """
        rma = self.filtered(lambda r: r.delivered_qty == 0)
        if rma:
            rma.write({'state': 'received'})

    def update_replaced_state(self):
        """ Invoked by:
         [stock.move]._action_done
         [stock.move].unlink
         [stock.move]._action_cancel
         """
        rma = self.filtered(
            lambda r: (r.state == 'waiting_replacement'
                       and 0 >= r.remaining_qty_to_done == r.remaining_qty))
        if rma:
            rma.write({'state': 'replaced'})

    def update_returned_state(self):
        """ Invoked by [stock.move]._action_done"""
        rma = self.filtered(
            lambda r: (r.state == 'waiting_return'
                       and r.remaining_qty_to_done <= 0))
        if rma:
            rma.write({'state': 'returned'})
