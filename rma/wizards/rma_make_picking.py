# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

import time
from openerp import models, fields, exceptions, api, _
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT
import openerp.addons.decimal_precision as dp


class RmaMakePicking(models.TransientModel):
    _name = 'rma_make_picking.wizard'
    _description = 'Wizard to create pickings from rma lines'

    @api.returns('rma.order.line')
    def _prepare_item(self, line):
        route = None
        if line.type == 'customer':
            route = line.operation_id.route_customer.id
        elif line.type == 'supplier':
            route = line.operation_id.route_supplier.id
        elif line.type == 'dropship':
            route = line.operation_id.route_dropship.id
        if not route:
            raise ValidationError(_('No route define for this '
                                  'operation'))

        values = {'product_id': line.product_id.id,
                  'name': line.name,
                  'product_qty': line.product_qty,
                  'uom_id': line.uom_id.id,
                  'state': line.state,
                  'type': line.type,
                  'company_id': line.company_id.id,
                  'operation_id': line.operation_id.id,
                  'invoice_line_id': line.invoice_line_id.id,
                  'partner_address_id': line.partner_address_id.id,
                  'qty_to_receive': line.qty_to_receive,
                  'route_id': route,
                  'is_dropship': line.is_dropship,
                  'qty_to_deliver': line.qty_to_deliver,
                  'line_id': line.id,
                  'wiz_id': self.env.context['active_id']}
        return values

    @api.model
    def default_get(self, fields):
        """Default values for wizard, if there is more than one supplier on
        lines the supplier field is empty otherwise is the unique line
        supplier.
        """
        res = super(RmaMakePicking, self).default_get(fields)
        rma_line_obj = self.env['rma.order.line']
        rma_line_ids = self.env.context['active_ids'] or []
        active_model = self.env.context['active_model']

        if not rma_line_ids:
            return res
        assert active_model == 'rma.order.line', \
            'Bad context propagation'

        items = []
        lines = rma_line_obj.browse(rma_line_ids)
        for line in lines:
            items.append([0, 0, self._prepare_item(line)])
        res['item_ids'] = items
        return res

    item_ids = fields.One2many(
        'rma_make_picking.wizard.item',
        'wiz_id', string='Items')

    def find_procurement_group(self, line):
        return self.env['procurement.group'].search([('rma_id', '=',
                                                      line.rma_id.id)])

    def _get_procurement_group_data(self, line):
        group_data = {
            'name': line.name,
            'rma_id': line.rma_id.id,
        }
        return group_data

    @api.model
    def _get_address(self, line, picking_type):
        if line.is_dropship and picking_type == 'outgoing':
            delivery_address = line.partner_address_id.id
        else:
            if line.rma_id.delivery_address_id:
                delivery_address = line.rma_id.delivery_address_id.id
            else:
                seller = line.product_id.seller_ids.filtered(
                    lambda p: p.name == line.invoice_line_id.invoice_id.
                        partner_id)
                partner = seller.warranty_return_address
                delivery_address = partner.id
        return delivery_address

    @api.model
    def _get_procurement_data(self, line, group, qty, picking_type):
        # incoming means returning products
        if picking_type == 'incoming':
            if line.type == 'customer':
                if line.is_dropship:
                    location = self.env.ref('stock.stock_location_suppliers')
                else:
                    location = line.rma_id.warehouse_id.lot_rma_id
            else:
                if line.is_dropship:
                    location = self.env.ref('stock.stock_location_customers')
                else:
                    location = line.rma_id.warehouse_id.lot_rma_id

        else:
            # delivery order
            if line.type == 'customer':
                location = self.env.ref('stock.stock_location_customers')
            else:
                if line.is_dropship:
                    location = self.env.ref('stock.stock_location_suppliers')
                else:
                    location = self.env.ref('stock.stock_location_suppliers')
        warehouse = line.rma_id.warehouse_id
        delivery_address = self._get_address(line, picking_type)

        procurement_data = {
            'name': line.operation_id.name,
            'group_id': group.id,
            'origin': line.rma_id.name,
            'warehouse_id': warehouse.id,
            'date_planned': time.strftime(DT_FORMAT),
            'product_id': line.product_id.id,
            'product_qty': qty,
            'partner_dest_id': delivery_address,
            'product_uom': line.product_id.product_tmpl_id.uom_id.id,
            'location_id': location.id,
            'rma_line_id': line.line_id.id,
            'route_ids': [(4, line.route_id.id)]
        }
        return procurement_data

    @api.model
    def _create_procurement(self, rma_line, picking_type):
        group = self.find_procurement_group(rma_line)
        if not group:
            procurement_group = self._get_procurement_group_data(rma_line)
            group = self.env['procurement.group'].create(procurement_group)
        if picking_type == 'incoming':
            qty = rma_line.qty_to_receive
        else:
            qty = rma_line.qty_to_deliver
        procurement_data = self._get_procurement_data(
            rma_line, group, qty, picking_type)
        # create picking
        procurement = self.env['procurement.order'].create(procurement_data)
        procurement.run()
        return procurement.id

    @api.multi
    def action_create_picking(self):
        """Method called when the user clicks on create picking"""
        picking_type = self.env.context.get('picking_type')
        procurement_list = []
        for line in self.item_ids:
            if line.state != 'approved':
                raise exceptions.Warning(
                    _('RMA %s is not approved') %
                    line.rma_id.name)
            if line.operation_id.shipment_type == 'no' and picking_type == \
                    'incoming':
                raise exceptions.Warning(
                    _('No shipments needed for this operation'))
            if line.operation_id.delivery_type == 'no' and picking_type == \
                    'outgoing':
                raise exceptions.Warning(
                    _('No deliveries needed for this operation'))
            procurement = self._create_procurement(line, picking_type)
            procurement_list.append(procurement)
        procurements = self.env['procurement.order'].browse(procurement_list)
        action = procurements.do_view_pickings()
        return action

    @api.multi
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}


class RmaMakePickingItem(models.TransientModel):
    _name = "rma_make_picking.wizard.item"
    _description = "Items to receive"

    wiz_id = fields.Many2one(
        'rma_make_picking.wizard',
        string='Wizard', required=True)
    line_id = fields.Many2one('rma.order.line',
                              string='RMA order Line',
                              readonly=True)
    rma_id = fields.Many2one('rma.order',
                             related='line_id.rma_id',
                             string='RMA',
                             readonly=True)
    type = fields.Selection(
        [('customer', 'Customer'), ('supplier', 'Supplier'), ('dropship',
                                                              'Dropship')])
    product_id = fields.Many2one('product.product', string='Product',
                                 readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('to_approve', 'To Approve'),
                              ('approved', 'Approved'),
                              ('done', 'Done')])
    company_id = fields.Many2one('res.company')
    name = fields.Char(string='Description', required=True)
    operation_id = fields.Many2one(comodel_name="rma.operation")
    route_id = fields.Many2one(
        'stock.location.route', string='Route')
    partner_address_id = fields.Many2one(
        'res.partner', readonly=True,
        string='Partner Address',
        help="This address of the supplier in case of Customer RMA operation "
             "dropship. The address of the customer in case of Supplier RMA "
             "operation dropship")
    product_qty = fields.Float(
        string='Quantity Ordered', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True)
    qty_to_receive = fields.Float(
        string='Quantity to Receive',
        digits=dp.get_precision('Product Unit of Measure'))
    qty_to_deliver = fields.Float(
        string='Quantity To Deliver',
        digits=dp.get_precision('Product Unit of Measure'))
    uom_id = fields.Many2one('product.uom', string='Unit of Measure',
                             readonly=True)
    invoice_line_id = fields.Many2one('account.invoice.line',
                                      string='Invoice Line')
    is_dropship = fields.Boolean(string="Dropship")
