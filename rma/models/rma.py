# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from openerp import _, api, fields, models
from openerp.addons import decimal_precision as dp
from openerp.exceptions import UserError


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
        required=True,
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
        picking_list = []
        for line in self.rma_line_ids:
            for move in line.move_ids:
                if move.picking_id.picking_type_id.code == 'incoming':
                    picking_list.append(move.picking_id.id)
        self.in_shipment_count = len(list(set(picking_list)))

    @api.one
    def _compute_invoice_count(self):
        invoice_list = []
        for line in self.rma_line_ids:
            invoice_list.append(line.invoice_id.id)
        self.invoice_count = len(list(set(invoice_list)))

    @api.one
    def _compute_out_shipment_count(self):
        picking_list = []
        for line in self.rma_line_ids:
            for move in line.move_ids:
                if move.picking_id.picking_type_id.code == 'outgoing':
                    if move.picking_id:
                        picking_list.append(move.picking_id.id)
        self.out_shipment_count = len(list(set(picking_list)))

    @api.one
    def _compute_line_count(self):
        self.line_count = len(self.rma_line_ids)

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

    def _prepare_rma_line_from_inv_line(self, line):
        data = {
            'invoice_line_id': line.id,
            'product_id': line.product_id.id,
            'name': line.name,
            'origin': line.invoice_id.number,
            'uom_id': line.uom_id.id,
            'operation': 'replace',
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
        for line in self.rma_line_ids:
            for move in line.move_ids:
                if move.picking_id.picking_type_id.code == 'incoming':
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
        for line in self.rma_line_ids:
            for move in line.move_ids:
                if move.picking_id.picking_type_id.code == 'outgoing':
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

    @api.multi
    def action_rma_approve(self):
        for rec in self:
            rec.state = 'approved'

    @api.multi
    def action_rma_done(self):
        for rec in self:
            rec.state = 'done'
            return True

    @api.multi
    def action_view_lines(self):
        """
        This function returns an action that display existing vendor refund
        bills of given purchase order id.
        When only one found, show the vendor bill immediately.
        """
        action = self.env.ref('rma.action_rma_customer_lines')
        result = action.read()[0]
        lines = self.rma_line_ids

        # choose the view_mode accordingly
        if len(lines) != 1:
            result['domain'] = "[('id', 'in', " + \
                               str(lines.ids) + ")]"
        elif len(lines) == 1:
            res = self.env.ref('rma.view_rma_line_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = lines.id
        return result


class RmaOrderLine(models.Model):
    _name = "rma.order.line"
    _order = "sequence"

    @api.one
    @api.depends('move_ids.state', 'state', 'operation', 'type')
    def _compute_qty_incoming(self):
        qty = 0.0
        for move in self.move_ids:
            if move.state not in ('done', 'cancel') and (
                    move.picking_id.picking_type_id.code == 'incoming'):
                qty += move.product_qty
        self.qty_incoming = qty

    @api.one
    @api.depends('move_ids.state', 'state', 'operation', 'type')
    def _compute_qty_to_receive(self):
        qty = 0.0
        if self.operation in ('repair', 'replace') or self.type == \
                "customer":
            for move in self.move_ids:
                if move.state == 'done' and (
                        move.picking_id.picking_type_id.code == 'incoming'):
                    qty += move.product_qty
            self.qty_to_receive = self.product_qty - qty
        else:
            self.qty_to_receive = qty

    @api.one
    @api.depends('move_ids.state', 'state', 'operation', 'type')
    def _compute_qty_to_deliver(self):
        qty = 0.0
        if self.operation in ('repair', 'replace') or self.type == \
                "supplier":
            for move in self.move_ids:
                if move.state == 'done' and \
                        move.picking_id.picking_type_id.code == 'outgoing':
                    qty += move.product_qty
            self.qty_to_deliver = self.product_qty - qty
        else:
            self.qty_to_deliver = qty

    @api.one
    @api.depends('move_ids.state', 'state', 'operation', 'type')
    def _compute_qty_received(self):
        qty = 0.0
        for move in self.move_ids:
            if move.state == 'done'and move.picking_id.picking_type_id.code \
                    == 'incoming':
                qty += move.product_qty
        self.qty_received = qty

    @api.one
    @api.depends('move_ids.state', 'state', 'operation', 'type')
    def _compute_qty_outgoing(self):
        qty = 0.0
        for move in self.move_ids:
            if move.state not in ('done', 'cancel') and (
                    move.picking_id.picking_type_id.code == 'outgoing'):
                qty += move.product_qty
        self.qty_outgoing = qty

    @api.one
    @api.depends('move_ids.state', 'state', 'operation', 'type')
    def _compute_qty_delivered(self):
        qty = 0.0
        for move in self.move_ids:
            if move.state == 'done' and (
                    move.picking_id.picking_type_id.code == 'outgoing'):
                qty += move.product_qty
        self.qty_delivered = qty

    @api.one
    @api.depends('refund_line_id', 'state', 'operation', 'type')
    def _compute_qty_refunded(self):
        qty = 0.0
        if self.refund_line_id:
            if self.refund_line_id.invoice_id.state != 'cancel':
                qty += self.refund_line_id.quantity
        self.qty_refunded = qty

    @api.one
    @api.depends('invoice_line_id', 'state', 'operation', 'type')
    def _compute_qty_to_refund(self):
        qty = 0.0
        if self.operation == 'refund':
            if self.invoice_line_id:
                if self.invoice_line_id.invoice_id.state != 'cancel':
                    qty += self.product_qty
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

    move_count = fields.Integer(compute=_compute_move_count,
                                string='# of Moves', copy=False, default=0)

    name = fields.Text(string='Description', required=True)
    origin = fields.Char(string='Source Document',
                         help="Reference of the document that produced "
                              "this rma.")
    state = fields.Selection(related='rma_id.state')
    operation = fields.Selection([
        ('refund', 'Refund'), ('repair', 'Receive and repair'),
        ('replace', 'Replace')], string="Operation", readonly=True,
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
        self.operation = self.product_id.categ_id.id

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
