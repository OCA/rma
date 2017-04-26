# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from openerp import _, api, fields, models
from openerp.addons import decimal_precision as dp
from openerp.exceptions import UserError
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import math
from datetime import datetime
import calendar


class RmaOrder(models.Model):
    _name = "rma.order"
    _inherit = ['mail.thread']

    @api.model
    def _default_warehouse_id(self):
        company = self.env.user.company_id.id
        warehouse_ids = self.env['stock.warehouse'].search(
            [('company_id', '=', company)], limit=1)
        return warehouse_ids

    @api.model
    def _get_default_type(self):
        if 'supplier' in self.env.context:
            return "supplier"
        else:
            return "customer"

    name = fields.Char(string='Reference/Description', index=True,
                       readonly=True,
                       states={'progress': [('readonly', False)]},
                       copy=False)
    type = fields.Selection(
        [('customer', 'Customer'), ('supplier', 'Supplier')],
        string="Type", required=True, default=_get_default_type, readonly=True)
    reference = fields.Char(string='Reference',
                            help="The partner reference of this RMA order.",
                            readonly=True,
                            states={'draft': [('readonly', False)]})

    comment = fields.Text('Additional Information', readonly=True, states={
        'draft': [('readonly', False)]})
    delivery_address_id = fields.Many2one(
        'res.partner', readonly=True,
        states={'draft': [('readonly', False)]},
        string='Partner delivery address',
        help="This address will be used to "
        "deliver repaired or replacement products.")
    invoice_address_id = fields.Many2one(
        'res.partner', readonly=True,
        required=True,
        states={'draft': [('readonly', False)]},
        string='Partner invoice address',
        help="Invoice address for current rma order.")
    add_invoice_id = fields.Many2one('account.invoice', string='Add Invoice',
                                     ondelete='set null', readonly=True,
                                     states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'), ('to_approve', 'To Approve'),
                              ('approved', 'Approved'),
                              ('done', 'Done')], string='State', index=True,
                             default='draft')
    date_rma = fields.Datetime(string='RMA Date', index=True, copy=False)
    partner_id = fields.Many2one('res.partner', string='Partner',
                                 required=True, readonly=True,
                                 states={'draft': [('readonly', False)]})
    assigned_to = fields.Many2one('res.users', 'Assigned to',
                                  track_visibility='onchange')
    requested_by = fields.Many2one('res.users', 'Requested_by',
                                   track_visibility='onchange',
                                   default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)
    rma_line_ids = fields.One2many('rma.order.line', 'rma_id',
                                   string='RMA lines',
                                   copy=False)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
                                   required=True, readonly=True,
                                   states={'draft': [('readonly', False)]},
                                   default=_default_warehouse_id)

    @api.model
    def create(self, vals):
        if self.env.context.get('supplier'):
            vals['name'] = self.env['ir.sequence'].get('rma.order.supplier')
        else:
            vals['name'] = self.env['ir.sequence'].get('rma.order')

        return super(RmaOrder, self).create(vals)

    @api.one
    def _compute_invoice_refund_count(self):
        invoice_list = []
        for line in self.rma_line_ids:
            if line.refund_line_id:
                invoice_list.append(line.refund_line_id.invoice_id.id)
        self.invoice_refund_count = len(list(set(invoice_list)))

    @api.one
    def _compute_in_shipment_count(self):
        picking_ids = []
        suppliers = self.env.ref('stock.stock_location_suppliers')
        customers = self.env.ref('stock.stock_location_customers')
        for line in self.rma_line_ids:
            if line.type == 'customer':
                for move in line.move_ids:
                    if move.picking_id.location_id == customers:
                        picking_ids.append(move.picking_id.id)
            else:
                for move in line.move_ids:
                    if move.picking_id.location_id == suppliers:
                        picking_ids.append(move.picking_id.id)
        self.in_shipment_count = len(list(set(picking_ids)))

    @api.one
    def _compute_invoice_count(self):
        invoice_list = []
        for line in self.rma_line_ids:
            invoice_list.append(line.invoice_id.id)
        self.invoice_count = len(list(set(invoice_list)))

    @api.one
    def _compute_out_shipment_count(self):
        picking_ids = []
        suppliers = self.env.ref('stock.stock_location_suppliers')
        customers = self.env.ref('stock.stock_location_customers')
        for line in self.rma_line_ids:
            if line.type == 'customer':
                for move in line.move_ids:
                    if move.picking_id.location_id != customers:
                        picking_ids.append(move.picking_id.id)
            else:
                for move in line.move_ids:
                    if move.picking_id.location_id != suppliers:
                        picking_ids.append(move.picking_id.id)
        self.out_shipment_count = len(list(set(picking_ids)))

    @api.one
    def _compute_supplier_line_count(self):
        lines = self.rma_line_ids.filtered(
            lambda r: r.related_rma_line)
        related_lines = [line.related_rma_line for line in lines]
        self.supplier_line_count = len(related_lines)

    @api.one
    def _compute_line_count(self):
        self.line_count = len(self.rma_line_ids.filtered(
            lambda p: p.warranty_state != 'expired'))

    invoice_refund_count = fields.Integer(
        compute=_compute_invoice_refund_count,
        string='# of Refunds',
        copy=False)
    invoice_count = fields.Integer(compute=_compute_invoice_count,
                                   string='# of Incoming Shipments',
                                   copy=False)
    in_shipment_count = fields.Integer(compute=_compute_in_shipment_count,
                                       string='# of Invoices', copy=False)
    out_shipment_count = fields.Integer(compute=_compute_out_shipment_count,
                                        string='# of Outgoing Shipments',
                                        copy=False)
    line_count = fields.Integer(compute=_compute_line_count,
                                string='# of Outgoing Shipments',
                                copy=False)
    supplier_line_count = fields.Integer(compute=_compute_supplier_line_count,
                                         string='# of Outgoing Shipments',
                                         copy=False)

    def _prepare_rma_line_from_inv_line(self, line):
        data = {
            'invoice_line_id': line.id,
            'product_id': line.product_id.id,
            'name': line.name,
            'origin': line.invoice_id.number,
            'uom_id': line.uom_id.id,
            'operation_id': line.product_id.categ_id.rma_operation_id.id,
            'product_qty': line.quantity,
            'price_unit': line.invoice_id.currency_id.compute(
                line.price_unit, line.currency_id, round=False),
            'rma_id': self._origin.id
        }
        return data

    @api.onchange('add_invoice_id')
    def on_change_invoice(self):
        if not self.add_invoice_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.add_invoice_id.partner_id.id
        new_lines = self.env['rma.order.line']
        for line in self.add_invoice_id.invoice_line_ids:
            # Load a PO line only once
            if line in self.rma_line_ids.mapped('invoice_line_id'):
                continue
            data = self._prepare_rma_line_from_inv_line(line)
            new_line = new_lines.new(data)
            new_lines += new_line

        self.rma_line_ids += new_lines
        self.date_rma = fields.Datetime.now()
        self.delivery_address_id = self.add_invoice_id.partner_id.id
        self.invoice_address_id = self.add_invoice_id.partner_id.id
        self.add_invoice_id = False
        return {}

    @api.multi
    def action_view_invoice_refund(self):
        """
        This function returns an action that display existing vendor refund
        bills of given purchase order id.
        When only one found, show the vendor bill immediately.
        """
        action = self.env.ref('account.action_invoice_tree2')
        result = action.read()[0]
        invoice_list = []
        for line in self.rma_line_ids:
            invoice_list.append(line.refund_line_id.invoice_id.id)
        invoice_ids = list(set(invoice_list))
        # choose the view_mode accordingly
        if len(invoice_ids) != 1:
            result['domain'] = "[('id', 'in', " + \
                               str(invoice_ids) + ")]"
        elif len(invoice_ids) == 1:
            res = self.env.ref('account.invoice_supplier_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = invoice_ids[0]
        return result

    @api.multi
    def action_view_invoice(self):
        if self.type == "supplier":
            action = self.env.ref('account.action_invoice_tree2')
        else:
            action = self.env.ref('account.action_invoice_tree')
        result = action.read()[0]
        invoice_list = []
        for line in self.rma_line_ids:
            invoice_list.append(line.invoice_id.id)
        invoice_ids = list(set(invoice_list))
        # choose the view_mode accordingly
        if len(invoice_ids) != 1:
            result['domain'] = "[('id', 'in', " + \
                               str(invoice_ids) + ")]"
        elif len(invoice_ids) == 1:
            if self.type == "supplier":
                res = self.env.ref('account.invoice_supplier_form', False)
            else:
                res = self.env.ref('account.invoice_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = invoice_ids[0]
        return result

    @api.multi
    def action_view_in_shipments(self):
        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]
        picking_ids = []
        suppliers = self.env.ref('stock.stock_location_suppliers')
        customers = self.env.ref('stock.stock_location_customers')
        for line in self.rma_line_ids:
            if line.type == 'customer':
                for move in line.move_ids:
                    if move.picking_id.location_id == customers:
                        picking_ids.append(move.picking_id.id)
            else:
                for move in line.move_ids:
                    if move.picking_id.location_id == suppliers:
                        picking_ids.append(move.picking_id.id)
        shipments = list(set(picking_ids))
        # choose the view_mode accordingly
        if len(shipments) != 1:
            result['domain'] = "[('id', 'in', " + \
                               str(shipments) + ")]"
        elif len(shipments) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = shipments[0]
        return result

    @api.multi
    def action_view_out_shipments(self):
        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]
        picking_ids = []
        suppliers = self.env.ref('stock.stock_location_suppliers')
        customers = self.env.ref('stock.stock_location_customers')
        for line in self.rma_line_ids:
            if line.type == 'customer':
                for move in line.move_ids:
                    if move.picking_id.location_id != customers:
                        picking_ids.append(move.picking_id.id)
            else:
                for move in line.move_ids:
                    if move.picking_id.location_id != suppliers:
                        picking_ids.append(move.picking_id.id)
        shipments = list(set(picking_ids))
        # choose the view_mode accordingly
        if len(shipments) != 1:
            result['domain'] = "[('id', 'in', " + \
                               str(shipments) + ")]"
        elif len(shipments) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = shipments[0]
        return result

    @api.multi
    def action_rma_to_approve(self):
        for rec in self:
            rec.state = 'to_approve'
        return True

    @api.multi
    def action_rma_draft(self):
        for rec in self:
            rec.state = 'draft'
        return True

    @api.model
    def _create_supplier_rma(self, origin_rma, lines):
        partners = lines.mapped('partner_address_id')
        for partner in partners:
            existing_rmas = self.env['rma.order'].search(
                [('partner_id', '=', partner.id),
                 ('state', '=', 'draft'),
                 ('type', '=', 'supplier')])
            if not len(existing_rmas):
                rma_values = {'partner_id': partner.id,
                              'delivery_address_id': partner.id,
                              'invoice_address_id': partner.id,
                              'type': 'supplier',
                              'assigned_to': origin_rma.assigned_to.id,
                              'requested_by': origin_rma.requested_by.id,
                              'date_rma': origin_rma.date_rma,
                              'warehouse_id': origin_rma.warehouse_id.id}
                rma_id = self.env['rma.order'].create(rma_values)
            else:
                rma_id = existing_rmas[0]
            for line in lines.filtered(
                    lambda p: p.partner_address_id == partner):
                line_values = {'origin': origin_rma.name,
                               'name': line.name,
                               'partner_address_id':
                                   origin_rma.delivery_address_id.id,
                               'product_id': line.product_id.id,
                               'related_rma_line': line.id,
                               'operation_id': line.operation_id.id,
                               'product_qty': line.product_qty,
                               'rma_id': rma_id.id}
                new_line = self.env['rma.order.line'].create(line_values)
                line.write({'related_rma_line': new_line.id})
        return True

    @api.multi
    def action_rma_approve(self):
        # pass the supplier address in case this is a customer RMA
        for rec in self:
            rec.state = 'approved'
            # Only customer RMA can create supplier RMA
            if rec.type == 'customer':
                lines = rec.rma_line_ids.filtered(lambda p: p.is_dropship)
                if lines:
                    self._create_supplier_rma(rec, lines)

    @api.multi
    def action_rma_done(self):
        for rec in self:
            rec.state = 'done'
            return True

    @api.multi
    def action_view_lines(self):
        action = self.env.ref('rma.action_rma_customer_lines')
        result = action.read()[0]
        lines = self.rma_line_ids.filtered(
            lambda p: p.warranty_state != 'expired')

        # choose the view_mode accordingly
        if len(lines) != 1:
            result['domain'] = "[('id', 'in', " + \
                               str(lines.ids) + ")]"
        elif len(lines) == 1:
            res = self.env.ref('rma.view_rma_line_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = lines.id
        return result

    @api.multi
    def action_view_supplier_lines(self):
        action = self.env.ref('rma.action_rma_supplier_lines')
        result = action.read()[0]
        lines = self.rma_line_ids.filtered(
            lambda r: r.related_rma_line)
        related_lines = [line.related_rma_line.id for line in lines]
        # choose the view_mode accordingly
        if len(lines) != 1:
            result['domain'] = "[('id', 'in', " + \
                               str(related_lines) + ")]"
        elif len(lines) == 1:
            res = self.env.ref('rma.view_rma_line_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = related_lines[0]
        return result


class RmaOrderLine(models.Model):
    _name = "rma.order.line"
    _order = "sequence"

    @api.one
    @api.depends('move_ids.state', 'state', 'operation_id', 'type')
    def _compute_qty_incoming(self):
        qty = 0.0
        suppliers = self.env.ref('stock.stock_location_suppliers')
        customers = self.env.ref('stock.stock_location_customers')
        for move in self.move_ids.filtered(
                        lambda m: m.state not in ('done', 'cancel')):
            if self.type == 'customer':
                if move.location_id == customers:
                    qty += move.product_qty
            else:
                if move.location_id == suppliers:
                    qty += move.product_qty
        self.qty_incoming = qty

    @api.one
    @api.depends('move_ids.state', 'state', 'operation_id', 'type')
    def _compute_qty_to_receive(self):
        qty = 0.0
        suppliers = self.env.ref('stock.stock_location_suppliers')
        customers = self.env.ref('stock.stock_location_customers')
        if self.operation_id.type in ('repair', 'replace'):
            for move in self.move_ids.filtered(
                    lambda m: m.state == 'done'):
                if self.type == 'customer':
                    if move.location_id == customers:
                        qty += move.product_qty
                else:
                    if move.location_id == suppliers:
                        qty += move.product_qty
            self.qty_to_receive = self.product_qty - qty
        else:
            self.qty_to_receive = qty

    @api.one
    @api.depends('move_ids.state', 'state', 'operation_id', 'type')
    def _compute_qty_to_deliver(self):
        qty = 0.0
        suppliers = self.env.ref('stock.stock_location_suppliers')
        customers = self.env.ref('stock.stock_location_customers')
        if self.operation_id.is_dropship:
            self.qty_to_deliver = - self.qty_delivered
        elif self.operation_id.type in ('repair', 'replace'):
            for move in self.move_ids.filtered(
                    lambda m: m.state == 'done'):
                if self.type == 'customer':
                    if move.location_id != customers:
                        qty += move.product_qty
                else:
                    if move.location_id != suppliers:
                        qty += move.product_qty
            self.qty_to_deliver = self.product_qty - qty
        else:
            self.qty_to_deliver = qty

    @api.one
    @api.depends('move_ids.state', 'state', 'operation_id', 'type')
    def _compute_qty_received(self):
        qty = 0.0
        suppliers = self.env.ref('stock.stock_location_suppliers')
        customers = self.env.ref('stock.stock_location_customers')
        for move in self.move_ids.filtered(
                        lambda m: m.state == 'done'):
            if self.type == 'customer':
                if move.location_id == customers:
                    qty += move.product_qty
            else:
                if move.location_id == suppliers:
                    qty += move.product_qty
        self.qty_received = qty

    @api.one
    @api.depends('move_ids.state', 'state', 'operation_id', 'type')
    def _compute_qty_outgoing(self):
        qty = 0.0
        suppliers = self.env.ref('stock.stock_location_suppliers')
        customers = self.env.ref('stock.stock_location_customers')
        for move in self.move_ids.filtered(
                lambda m: m.state not in ('done', 'cancel')):
            if self.type == 'customer':
                if move.location_id != customers:
                    qty += move.product_qty
            else:
                if move.location_id != suppliers:
                    qty += move.product_qty
        self.qty_outgoing = qty

    @api.one
    @api.depends('move_ids.state', 'state', 'operation_id', 'type')
    def _compute_qty_delivered(self):
        qty = 0.0
        suppliers = self.env.ref('stock.stock_location_suppliers')
        customers = self.env.ref('stock.stock_location_customers')
        for move in self.move_ids.filtered(
                lambda m: m.state == 'done'):
            if self.type == 'customer':
                if move.location_id != customers:
                    qty += move.product_qty
            else:
                if move.location_id != suppliers:
                    qty += move.product_qty
        self.qty_delivered = qty

    @api.one
    @api.depends('refund_line_id', 'state', 'operation_id', 'type')
    def _compute_qty_refunded(self):
        qty = 0.0
        if self.refund_line_id:
            if self.refund_line_id.invoice_id.state != 'cancel':
                qty += self.refund_line_id.quantity
        self.qty_refunded = qty

    @api.one
    @api.depends('invoice_line_id', 'state', 'operation_id', 'type',
                 'refund_line_id')
    def _compute_qty_to_refund(self):
        qty = 0.0
        if self.operation_id.type == 'refund':
            qty = self.product_qty
            if self.refund_line_id:
                if self.refund_line_id.invoice_id.state != 'cancel':
                    qty -= self.refund_line_id.quantity
        self.qty_to_refund = qty

    @api.one
    def _compute_move_count(self):
        move_list = []
        for move in self.move_ids:
            move_list.append(move.id)
        self.move_count = len(list(set(move_list)))

    @api.model
    def _default_dest_location_id(self):
        if self.rma_id.warehouse_id.lot_rma_id:
            return self.rma_id.warehouse_id.lot_rma_id.id
        else:
            return False

    @api.model
    def _default_src_location_id(self):
        if self.type == 'customer':
            if self.rma_id.partner_id.property_stock_customer:
                return lines.rma_id.partner_id.property_stock_customer.id
            else:
                return False
        else:
            if self.rma_id.partner_id.property_stock_supplier:
                return lines.rma_id.partner_id.property_stock_supplier.id
            else:
                return False

    @api.one
    @api.depends('invoice_line_id')
    def _compute_warranty(self):
        limit = False
        state = "undefined"
        line = self.invoice_line_id
        invoice_date = line.invoice_id.date_invoice
        if self.type == 'supplier':
            seller = line.product_id.seller_ids.filtered(
                lambda p: p.name == line.invoice_id.partner_id)
            warranty = seller.warranty_duration or False
        else:
            warranty = line.product_id.warranty

        if warranty and invoice_date:
            limit = datetime.strptime(
                invoice_date, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(
                months=int(warranty))
        if limit and warranty > 0:
            if limit < datetime.now():
                state = 'expired'
            else:
                state = 'valid'
        if limit:
            self.limit = datetime.strftime(limit, DEFAULT_SERVER_DATE_FORMAT)
        self.warranty_state = state

    move_count = fields.Integer(compute=_compute_move_count,
                                string='# of Moves', copy=False, default=0)
    name = fields.Text(string='Description', required=True)
    origin = fields.Char(string='Source Document',
                         help="Reference of the document that produced "
                              "this rma.")
    state = fields.Selection(related='rma_id.state')
    operation_id = fields.Many2one(
        comodel_name="rma.operation", string="Operation", readonly=True,
        required=True, index=True, states={'draft': [('readonly', False)]})

    invoice_line_id = fields.Many2one('account.invoice.line',
                                      string='Invoice Line',
                                      ondelete='restrict',
                                      index=True)
    refund_line_id = fields.Many2one('account.invoice.line',
                                     string='Refund Line',
                                     ondelete='restrict',
                                     copy=False,
                                     index=True, readonly=True)
    invoice_id = fields.Many2one('account.invoice', string='Source',
                                 related='invoice_line_id.invoice_id',
                                 index=True, readonly=True)
    assigned_to = fields.Many2one('res.users', related='rma_id.assigned_to')
    requested_by = fields.Many2one('res.users', related='rma_id.requested_by')
    partner_id = fields.Many2one('res.partner', related='rma_id.partner_id')
    sequence = fields.Integer(default=10,
                              help="Gives the sequence of this line "
                              "when displaying the rma.")
    rma_id = fields.Many2one('rma.order', string='RMA',
                             ondelete='cascade')
    uom_id = fields.Many2one('product.uom', string='Unit of Measure')
    product_id = fields.Many2one('product.product', string='Product',
                                 ondelete='restrict', index=True,
                                 readonly=True,
                                 states={'draft': [('readonly', False)]})
    price_unit = fields.Monetary(string='Price Unit', readonly=True,
                                 states={'draft': [('readonly', False)]})
    move_ids = fields.One2many('stock.move', 'rma_id',
                               string='Stock Moves', readonly=True,
                               states={'draft': [('readonly', False)]},
                               copy=False)
    currency_id = fields.Many2one('res.currency', string="Currency")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)
    type = fields.Selection(related='rma_id.type')
    route_id = fields.Many2one('stock.location.route', string='Route',
                               domain=[('rma_selectable', '=', True)])
    limit = fields.Date('Warranty Expiry Date', compute=_compute_warranty)
    warranty_state = fields.Selection([('valid', _("Valid")),
                                       ('expired', _("Expired")),
                                       ('undefined', _("Undefined"))],
                                      string='Warranty',
                                      compute=_compute_warranty)
    is_dropship = fields.Boolean(related="operation_id.is_dropship")
    related_rma_line = fields.Many2one(
        'rma.order.line', string='Parent RMA line', ondelete='cascade')
    # rma_ids = fields.One2many('rma.order.line', 'parent_rma')
    partner_address_id = fields.Many2one(
        'res.partner', readonly=True,
        states={'draft': [('readonly', False)]},
        string='Partner Address',
        help="This address of the supplier in case of Customer RMA operation "
             "dropship. The address of the customer in case of Supplier RMA "
             "operation dropship")
    product_qty = fields.Float(
        string='Ordered Qty', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True,
        states={'draft': [('readonly', False)]})
    qty_to_receive = fields.Float(
        string='Qty To Receive',
        digits=dp.get_precision('Product Unit of Measure'),
        compute=_compute_qty_to_receive, store=True)
    qty_incoming = fields.Float(
        string='Incoming Qty', copy=False,
        readonly=True, digits=dp.get_precision('Product Unit of Measure'),
        compute=_compute_qty_incoming, store=True)
    qty_received = fields.Float(
        string='Qty Received', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        compute=_compute_qty_received,
        store=True)
    qty_to_deliver = fields.Float(
        string='Qty To Deliver', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True, compute=_compute_qty_to_deliver,
        store=True)
    qty_outgoing = fields.Float(
        string='Outgoing Qty', copy=False,
        readonly=True, digits=dp.get_precision('Product Unit of Measure'),
        compute=_compute_qty_outgoing,
        store=True)
    qty_delivered = fields.Float(
        string='Qty Delivered', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True, compute=_compute_qty_delivered,
        store=True)
    qty_to_refund = fields.Float(
        string='Qty To Refund', copy=False,
        digits=dp.get_precision('Product Unit of Measure'), readonly=True,
        compute=_compute_qty_to_refund, store=True)
    qty_refunded = fields.Float(
        string='Qty Refunded', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True, compute=_compute_qty_refunded, store=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.invoice_id:
            return
        self.name = self.product.partner_ref
        self.operation_id = self.product_id.categ_id.rma_operation_id.id

    @api.onchange('invoice_line_id')
    def _onchange_invoice_line_id(self):
        if not self.invoice_line_id:
            return
        self.origin = self.invoice_id.number

    @api.multi
    @api.constrains('invoice_line_id')
    def _check_duplicated_lines(self):
        for line in self:
            matching_inv_lines = self.env['account.invoice.line'].search([(
                'id', '=', line.invoice_line_id.id)])
            if len(matching_inv_lines) > 1:
                    raise UserError(
                        _("There's an rma for the invoice line %s "
                          "and invoice %s" %
                          (line.invoice_line_id,
                           line.invoice_line_id.invoice_id)))
        return {}

    @api.multi
    def action_view_invoice(self):
        action = self.env.ref('account.action_invoice_tree')
        result = action.read()[0]
        res = self.env.ref('account.invoice_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['view_id'] = res and res.id or False
        result['res_id'] = self.invoice_line_id.id
        result['target'] = 'new'
        return result

    @api.multi
    def action_view_refund(self):
        action = self.env.ref('account.action_invoice_tree2')
        result = action.read()[0]
        res = self.env.ref('account.invoice_supplier_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = self.refund_line_id.id
        result['view_id'] = res and res.id or False
        result['target'] = 'new'
        return result

    @api.multi
    def action_view_moves(self):
        action = self.env.ref('stock.action_move_form2')
        result = action.read()[0]
        moves = self.move_ids.ids
        # choose the view_mode accordingly
        if len(moves) != 1:
            result['domain'] = "[('id', 'in', " + \
                               str(moves) + ")]"
            result['target'] = 'new'
        elif len(moves) == 1:
            res = self.env.ref('stock.view_move_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = moves[0]
        return result


class RmaOperation(models.Model):
    _name = 'rma.operation'
    _description = 'RMA Operation'

    name = fields.Char('Description', required=True)
    code = fields.Char('Code', required=True)
    type = fields.Selection([
        ('refund', 'Refund'), ('repair', 'Receive and repair'),
        ('replace', 'Replace')], string="Type", required=True)
    route_customer = fields.Many2one(
        'stock.location.route', string='Route RMA Customer',
        domain=[('rma_selectable', '=', True)])
    route_supplier = fields.Many2one(
        'stock.location.route', string='Route RMA Supplier',
        domain=[('rma_selectable', '=', True)])
    is_dropship = fields.Boolean('Dropship')
    rma_line_ids = fields.One2many('rma.order.line', 'operation_id',
                                   'RMA lines')
