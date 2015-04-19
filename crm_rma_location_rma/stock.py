# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2013 Camptocamp
#    Copyright 2015 Vauxoo
#    Author: Yanina Aular
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields
from openerp import SUPERUSER_ID
# , api
from openerp.tools.translate import _


class stock_warehouse(models.Model):

    _inherit = "stock.warehouse"

    lot_rma_id = fields.Many2one('stock.location',
                                 'RMA Location')

    rma_out_type_id = fields.Many2one('stock.picking.type',
                                      'RMA Out Type')

    rma_in_type_id = fields.Many2one('stock.picking.type',
                                     'RMA In Type')

    rma_int_type_id = fields.Many2one('stock.picking.type',
                                      'RMA Internal Type')

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if vals is None:
            vals = {}

        data_obj = self.pool.get('ir.model.data')
        location_obj = self.pool.get('stock.location')

        context_with_inactive = context.copy()
        context_with_inactive['active_test'] = False
        # create view location for warehouse
        loc_vals = {'name': _(vals.get('code')),
                    'usage': 'view',
                    'location_id': data_obj.
                    get_object_reference(cr, uid,
                                         'stock',
                                         'stock_location_locations')[1]}
        if vals.get('company_id'):
            loc_vals['company_id'] = vals.get('company_id')
        wh_loc_id = location_obj.create(cr, uid, loc_vals, context=context)
        vals['view_location_id'] = wh_loc_id

        sub_locations = [
            {'name': _('RMA'), 'active': True,
             'field': 'lot_rma_id'},
            {'name': _('Refurbish'), 'active': True,
             'field': 'lot_refurbish_id'},
            {'name': _('Carrier Loss'), 'active': True,
             'field': 'lot_carrier_loss_id'},
            {'name': _('Breakage Loss'), 'active': True,
             'field': 'lot_breakage_loss_id'},
        ]
        for values in sub_locations:
            loc_vals = {
                'name': values['name'],
                'usage': 'internal',
                'location_id': wh_loc_id,
                'active': values['active'],
            }
            if vals.get('company_id'):
                loc_vals['company_id'] = vals.get('company_id')
            location_id = location_obj.\
                create(cr, uid, loc_vals, context=context_with_inactive)
            vals[values['field']] = location_id

        return super(stock_warehouse, self).\
            create(cr, uid, vals=vals, context=context)

    def create_sequences_and_picking_types(self, cr, uid,
                                           warehouse, context=None):

        super(stock_warehouse, self).\
            create_sequences_and_picking_types(cr, uid,
                                               warehouse,
                                               context=context)

        seq_obj = self.pool.get('ir.sequence')
        picking_type_obj = self.pool.get('stock.picking.type')
        # create new sequences
        in_seq_id = seq_obj.create(cr,
                                   SUPERUSER_ID,
                                   values={'name': warehouse.name
                                           + _(' Sequence in'),
                                           'prefix': warehouse.code
                                           + 'RMA/IN/', 'padding': 5},
                                   context=context)
        out_seq_id = seq_obj.create(cr,
                                    SUPERUSER_ID,
                                    values={'name': warehouse.name
                                            + _(' Sequence out'),
                                            'prefix': warehouse.code
                                            + 'RMA/OUT/', 'padding': 5},
                                    context=context)
        int_seq_id = seq_obj.create(cr,
                                    SUPERUSER_ID,
                                    values={'name': warehouse.name
                                            + _(' Sequence internal'),
                                            'prefix': warehouse.code
                                            + 'RMA/INT/',
                                            'padding': 5}, context=context)

        wh_stock_loc = warehouse.lot_rma_id
        wh_input_stock_loc = warehouse.wh_input_stock_loc_id
        wh_output_stock_loc = warehouse.wh_output_stock_loc_id

        # fetch customer and supplier locations, for references
        customer_loc, supplier_loc = self.\
            _get_partner_locations(cr, uid, warehouse.id, context=context)

        # create in, out, internal picking types for warehouse
        input_loc = wh_input_stock_loc
        if warehouse.reception_steps == 'one_step':
            input_loc = wh_stock_loc
        output_loc = wh_output_stock_loc
        if warehouse.delivery_steps == 'ship_only':
            output_loc = wh_stock_loc

        # choose the next available color for
        # the picking types of this warehouse
        color = 0
        available_colors = [c % 9 for c in
                            range(3, 12)]  # put flashy colors first
        all_used_colors = self.pool.get('stock.picking.type').\
            search_read(cr, uid, [('warehouse_id', '!=', False),
                                  ('color', '!=', False)],
                        ['color'], order='color')
        # don't use sets to preserve the list order
        for x in all_used_colors:
            if x['color'] in available_colors:
                available_colors.remove(x['color'])
        if available_colors:
            color = available_colors[0]

        # order the picking types with a sequence
        # allowing to have the following suit for
        # each warehouse: reception, internal, pick, pack, ship.
        max_sequence = self.pool.get('stock.picking.type').\
            search_read(cr, uid, [], ['sequence'], order='sequence desc')
        max_sequence = max_sequence and max_sequence[0]['sequence'] or 0

        in_type_id = picking_type_obj.create(cr, uid, vals={
            'name': _('RMA Receipts'),
            'warehouse_id': warehouse.id,
            'code': 'outgoing',
            'sequence_id': out_seq_id,
            'default_location_src_id': customer_loc.id,
            'default_location_dest_id': wh_stock_loc.id,
            'sequence': max_sequence + 4,
            'color': color}, context=context)
        out_type_id = picking_type_obj.create(cr, uid, vals={
            'name': _('RMA Delivery Orders'),
            'warehouse_id': warehouse.id,
            'code': 'incoming',
            'sequence_id': in_seq_id,
            'return_picking_type_id': in_type_id,
            'default_location_src_id': wh_stock_loc.id,
            'default_location_dest_id': supplier_loc.id,
            'sequence': max_sequence + 1,
            'color': color}, context=context)
        picking_type_obj.write(cr, uid,
                               [in_type_id],
                               {'return_picking_type_id': out_type_id},
                               context=context)
        int_type_id = picking_type_obj.create(cr, uid, vals={
            'name': _('RMA Internal Transfers'),
            'warehouse_id': warehouse.id,
            'code': 'internal',
            'sequence_id': int_seq_id,
            'default_location_src_id': wh_stock_loc.id,
            'default_location_dest_id': wh_stock_loc.id,
            'active': True,
            'sequence': max_sequence + 2,
            'color': color}, context=context)

        # write picking types on WH
        vals = {
            'rma_in_type_id': in_type_id,
            'rma_out_type_id': out_type_id,
            'rma_int_type_id': int_type_id,
        }
        super(stock_warehouse, self).\
         write(cr, uid, warehouse.id, vals=vals, context=context)
