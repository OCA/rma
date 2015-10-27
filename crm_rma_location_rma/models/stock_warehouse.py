# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2013 Camptocamp
#    Copyright 2015 Vauxoo
#    Author: Yanina Aular
#            Osval Reyes
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

from openerp import _, api, fields, models


class StockWarehouse(models.Model):

    _inherit = "stock.warehouse"

    lot_rma_id = fields.Many2one('stock.location', 'RMA Location')
    rma_out_type_id = fields.Many2one('stock.picking.type', 'RMA Out Type')
    rma_in_type_id = fields.Many2one('stock.picking.type', 'RMA In Type')
    rma_int_type_id = fields.Many2one('stock.picking.type',
                                      'RMA Internal Type')

    @api.model
    def create_sequences_picking_types(self, warehouse):
        """
        Takes care of create picking types for internal,
        incoming and outgoing RMA
        """
        seq_obj = self.env['ir.sequence']
        picking_type_obj = self.env['stock.picking.type']
        # create new sequences

        if not warehouse.rma_in_type_id:
            in_seq_id = seq_obj.sudo().create(
                values={
                    'name': warehouse.name + _(' Sequence in'),
                    'prefix': warehouse.code + '/RMA/IN/',
                    'padding': 5
                })
        if not warehouse.rma_out_type_id:
            out_seq_id = seq_obj.sudo().create(
                values={
                    'name': warehouse.name + _(' Sequence out'),
                    'prefix': warehouse.code + '/RMA/OUT/',
                    'padding': 5
                })
        if not warehouse.rma_int_type_id:
            int_seq_id = seq_obj.sudo().create(
                values={
                    'name': warehouse.name + _(' Sequence internal'),
                    'prefix': warehouse.code + '/RMA/INT/',
                    'padding': 5
                })

        wh_stock_loc = warehouse.lot_rma_id

        # fetch customer and supplier locations, for references
        customer_loc, supplier_loc = self._get_partner_locations()

        # choose the next available color for
        # the picking types of this warehouse
        available_colors = [c % 9 for c in range(3, 12)]
        all_used_colors = self.env['stock.picking.type'].\
            search_read([('warehouse_id', '!=', False),
                         ('color', '!=', False)],
                        ['color'], order='color')
        # don't use sets to preserve the list order
        for col in all_used_colors:
            if col['color'] in available_colors:
                available_colors.remove(col['color'])

        color = available_colors[0] if available_colors else 0

        # order the picking types with a sequence
        # allowing to have the following suit for
        # each warehouse: reception, internal, pick, pack, ship.
        max_sequence = self.env['stock.picking.type'].\
            search_read([], ['sequence'], order='sequence desc')
        max_sequence = max_sequence and max_sequence[0]['sequence'] or 0

        in_type_id = warehouse.rma_in_type_id
        if not in_type_id:
            in_type_id = picking_type_obj.create(vals={
                'name': _('RMA Receipts'),
                'warehouse_id': warehouse.id,
                'code': 'incoming',
                'sequence_id': in_seq_id.id,
                'default_location_src_id': customer_loc.id,
                'default_location_dest_id': wh_stock_loc.id,
                'sequence': max_sequence + 4,
                'color': color})

        out_type_id = warehouse.rma_out_type_id
        if not out_type_id:
            out_type_id = picking_type_obj.create(vals={
                'name': _('RMA Delivery Orders'),
                'warehouse_id': warehouse.id,
                'code': 'outgoing',
                'sequence_id': out_seq_id.id,
                'return_picking_type_id': in_type_id.id,
                'default_location_src_id': wh_stock_loc.id,
                'default_location_dest_id': supplier_loc.id,
                'sequence': max_sequence + 1,
                'color': color})
            in_type_id.write({'return_picking_type_id': out_type_id.id})

        int_type_id = warehouse.rma_int_type_id
        if not int_type_id:
            int_type_id = picking_type_obj.create(vals={
                'name': _('RMA Internal Transfers'),
                'warehouse_id': warehouse.id,
                'code': 'internal',
                'sequence_id': int_seq_id.id,
                'default_location_src_id': wh_stock_loc.id,
                'default_location_dest_id': wh_stock_loc.id,
                'active': True,
                'sequence': max_sequence + 2,
                'color': color})

        # write picking types on WH
        vals = {
            'rma_in_type_id': in_type_id.id,
            'rma_out_type_id': out_type_id.id,
            'rma_int_type_id': int_type_id.id,
        }
        return vals

    @api.model
    def create_locations_rma(self, warehouse_id):
        """
        Create a RMA location for RMA movements that takes place when internal,
        outgoing or incoming pickings are made from/to this location
        """
        vals = {}

        location_obj = self.env['stock.location']
        context_with_inactive = self.env.context.copy()
        context_with_inactive['active_test'] = False
        view_location_id = warehouse_id.view_location_id.id

        if not warehouse_id.lot_rma_id:
            loc_vals = {
                'name': _('RMA'),
                'usage': 'internal',
                'location_id': view_location_id,
                'active': True,
            }
            if vals.get('company_id'):
                loc_vals['company_id'] = vals.get('company_id')
            location_id = location_obj.with_context(context_with_inactive).\
                create(loc_vals)
            vals['lot_rma_id'] = location_id.id

        return vals

    @api.model
    def create(self, vals):
        """
        Create Locations and picking types for warehouse
        """
        new_id_warehouse = super(StockWarehouse, self).create(vals=vals)
        new_vals = self.create_locations_rma(new_id_warehouse)
        new_id_warehouse.write(vals=new_vals)
        new_vals = self.create_sequences_picking_types(new_id_warehouse)
        new_id_warehouse.write(vals=new_vals)
        return new_id_warehouse
