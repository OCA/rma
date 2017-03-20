# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

import time
from openerp import models, fields, exceptions, api, _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT
import openerp.addons.decimal_precision as dp


class RmaMakePicking(models.TransientModel):
    _name = 'rma_make_picking.wizard'
    _description = 'Wizard to create pickings from rma lines'

    @api.model
    def _default_dest_location_id(self):
        if self.env.context.get('picking_type') == 'in':
            if self.warehouse_id:
                return self.warehouse_id.lot_rma_id.id
            if 'active_ids' in self.env.context:
                domain = [('id', 'in', self.env.context['active_ids'])]
                lines = self.env['rma.order.line']. \
                    search(domain, limit=1)
                return lines.rma_id.warehouse_id.lot_rma_id.id
        else:
            domain = [('id', 'in', self.env.context['active_ids'])]
            lines = self.env['rma.order.line']. \
                search(domain, limit=1)
            if lines.type == 'customer':
                return lines.rma_id.partner_id.property_stock_customer.id
            else:
                return lines.rma_id.partner_id.property_stock_supplier.id

    @api.model
    def _default_src_location_id(self):
        if self.env.context.get('picking_type') == 'out':
            if self.warehouse_id:
                return self.warehouse_id.lot_rma_id.id
            if 'active_ids' in self.env.context:
                domain = [('id', 'in', self.env.context['active_ids'])]
                lines = self.env['rma.order.line']. \
                    search(domain, limit=1)
                return lines.rma_id.warehouse_id.lot_rma_id.id
        else:
            domain = [('id', 'in', self.env.context['active_ids'])]
            lines = self.env['rma.order.line']. \
                search(domain, limit=1)
            if lines.type == 'supplier':
                return lines.rma_id.partner_id.property_stock_supplier.id
            else:
                return lines.rma_id.partner_id.property_stock_customer.id

    @api.model
    def _default_rma_warehouse(self):
        domain = [('id', 'in', self.env.context['active_ids'])]
        lines = self.env['rma.order.line']. \
            search(domain, limit=1)
        return lines.rma_id.warehouse_id.id

    @api.returns('rma.order.line')
    def _prepare_item(self, line):
        values = {'product_id': line.product_id.id,
                  'name': line.name,
                  'product_qty': line.product_qty,
                  'uom_id': line.uom_id.id,
                  'qty_to_receive': line.qty_to_receive,
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

    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Source Warehouse',
        default=_default_rma_warehouse,
        required=True,
        help="Warehouse where to take the replacement products for customers.",
    )

    src_location_id = fields.Many2one(
        'stock.location', string='Source Location',
        required=True,
        default=_default_src_location_id,
        help="Location where the returned products are from.")

    dest_location_id = fields.Many2one(
        'stock.location', string='Destination Location',
        required=True,
        default=_default_dest_location_id,
        help="Location where the returned products are from.")
    item_ids = fields.One2many(
        'rma_make_picking.wizard.item',
        'wiz_id', string='Items')

    def _get_picking_name(self):
        return 'RMA picking {}'.format(
            self.env.context.get('picking_type', 'in'))

    def _get_picking_note(self):
        return self._get_picking_name()

    def _get_picking_data(self, rma, picking_type, partner_id):
        return {
            'origin': rma.rma_id.name,
            'picking_type_id': picking_type.id,
            'move_type': 'one',  # direct
            'state': 'draft',
            'date': time.strftime(DT_FORMAT),
            'partner_id': partner_id,
            'company_id': rma.company_id.id,
            'location_id': self.src_location_id.id,
            'location_dest_id': self.dest_location_id.id,
            'note': self._get_picking_note(),
        }

    def _get_picking_line_data(self, rma, picking, line, qty):
        return {
            'name': line.product_id.name_template,
            'priority': '0',
            'date': time.strftime(DT_FORMAT),
            'date_expected': time.strftime(DT_FORMAT),
            'product_id': line.product_id.id,
            'product_uom_qty': qty,
            'product_uom': line.product_id.product_tmpl_id.uom_id.id,
            'partner_id': rma.rma_id.partner_id.id,
            'picking_id': picking.id,
            'state': 'draft',
            'price_unit': line.price_unit,
            'company_id': rma.company_id.id,
            'location_id': self.src_location_id.id,
            'location_dest_id': self.dest_location_id.id,
            'note': self._get_picking_note(),
            'rma_id': line.id
        }

    def _create_picking(self, rma, picking_type):
        warehouse_rec = self.warehouse_id
        if picking_type == 'in':
            if rma.type == 'customer':
                rma_picking_type = warehouse_rec.rma_cust_in_type_id
            else:
                rma_picking_type = warehouse_rec.rma_sup_in_type_id
            write_field = 'move_in_id'
        else:
            if rma.type == 'customer':
                rma_picking_type = warehouse_rec.rma_cust_out_type_id
            else:
                rma_picking_type = warehouse_rec.rma_sup_out_type_id
            write_field = 'move_out_id'

        if len(rma.rma_id.delivery_address_id):
            partner_id = rma.rma_id.delivery_address_id.id
        else:
            partner_id = rma.rma_id.partner_id.id

        # create picking
        picking = self.env['stock.picking'].create(
            self._get_picking_data(rma, rma_picking_type, partner_id))

        # Create picking lines
        for line in self.item_ids:
            if picking_type == 'in':
                qty = line.qty_to_receive
            else:
                qty = line.qty_to_deliver
            move = self.env['stock.move'].create(
                self._get_picking_line_data(rma, picking, line.line_id, qty))
            line.write({write_field: move.id})

        if picking:
            picking.signal_workflow('button_confirm')
            picking.action_assign()

        domain = ("[('picking_type_id', '=', %s), ('partner_id', '=', %s)]" %
                  (rma_picking_type.id, partner_id))

        view_id = self.env['ir.ui.view'].search(
            [('model', '=', 'stock.picking'),
             ('type', '=', 'form')])[0]
        return {
            'name': self._get_picking_name(),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id.id,
            'domain': domain,
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def action_create_picking(self):
        rma_line_ids = self.env['rma.order.line'].browse(
            self.env.context['active_ids'])
        picking_type = self.env.context.get('picking_type')
        for line in rma_line_ids:
            if line.state != 'approved':
                raise exceptions.Warning(
                    _('RMA %s is not approved') %
                    line.rma_id.name)
            if line.operation not in ('replace', 'repair') and \
                    picking_type == 'out' and line.type == 'customer':
                raise exceptions.Warning(
                    _('Only refunds allowed for at least one line'))
            if line.operation not in ('replace', 'repair') and \
                    picking_type == 'in' and line.type == 'supplier':
                raise exceptions.Warning(
                    _('Only refunds allowed for at least one line'))
            return self._create_picking(line, picking_type)

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
                              required=True,
                              readonly=True)
    rma_id = fields.Many2one('rma.order',
                             related='line_id.rma_id',
                             string='RMA',
                             readonly=True)
    product_id = fields.Many2one('product.product', string='Product',
                                 readonly=True)
    name = fields.Char(string='Description', required=True)
    product_qty = fields.Float(
        string='Quantity Ordered', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True)
    qty_to_receive = fields.Float(
        string='Quantity To Receive',
        digits=dp.get_precision('Product Unit of Measure'))
    qty_to_deliver = fields.Float(
        string='Quantity To Deliver',
        digits=dp.get_precision('Product Unit of Measure'))
    uom_id = fields.Many2one('product.uom', string='Unit of Measure',
                             readonly=True)
