# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2013 Camptocamp
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Joel Grand-Guillaume
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
    loss_loc_id = fields.Many2one('stock.location', 'Loss Location')
    lot_refurbish_id = fields.Many2one('stock.location',
                                       'Refurbished Location')
    rma_out_type_id = fields.Many2one('stock.picking.type', 'RMA Out Type')
    rma_in_type_id = fields.Many2one('stock.picking.type', 'RMA In Type')
    rma_int_type_id = fields.Many2one('stock.picking.type',
                                      'RMA Internal Type')
    rma_destruction_type_id = fields.Many2one('stock.picking.type',
                                              help='Picking type for products '
                                              'that will be destroyed')

    def compute_next_color(self):
        """Choose the next available color for
        the picking types of this warehouse
        """
        available_colors = [c % 9 for c in range(3, 12)]
        all_used_colors = self.env['stock.picking.type'].search_read(
            [('warehouse_id', '!=', False), ('color', '!=', False)],
            ['color'], order='color')
        for col in all_used_colors:
            if col['color'] in available_colors:
                available_colors.remove(col['color'])

        return available_colors[0] if available_colors else 0

    def create_sequence(self, warehouse_id, name, prefix, padding):
        return self.env['ir.sequence'].sudo().\
            create({
                'name': warehouse_id.name + name,
                'prefix': warehouse_id.code + prefix,
                'padding': padding,
                'company_id': warehouse_id.company_id.id
            })

    @api.model
    def create_sequences_picking_types(self, warehouse):
        """Takes care of create picking types for internal,
        incoming and outgoing RMA
        """
        picking_type = self.env['stock.picking.type']

        # create new sequences
        if not warehouse.rma_in_type_id:
            in_seq_id = self.create_sequence(
                warehouse, _(' Sequence in'), '/RMA/IN/', 5
            )

        if not warehouse.rma_out_type_id:
            out_seq_id = self.create_sequence(
                warehouse, _(' Sequence out'), '/RMA/OUT/', 5
            )

        if not warehouse.rma_int_type_id:
            int_seq_id = self.create_sequence(
                warehouse, _(' Sequence internal'), '/RMA/INT/', 5
            )

        if not warehouse.rma_destruction_type_id:
            destruction_seq_id = self.create_sequence(
                warehouse, _(' Sequence destruction'), '/DEST/', 5
            )

        loc_rma = warehouse.lot_rma_id
        loc_loss = warehouse.loss_loc_id

        # fetch customer and supplier locations, for references
        customer_loc, supplier_loc = self._get_partner_locations()

        color = self.compute_next_color()

        # order the picking types with a sequence
        # allowing to have the following suit for
        # each warehouse: reception, internal, pick, pack, ship.
        max_sequence = self.env['stock.picking.type'].\
            search_read([], ['sequence'], order='sequence desc')
        max_sequence = max_sequence and max_sequence[0]['sequence'] or 0

        in_type_id = warehouse.rma_in_type_id
        if not in_type_id:
            in_type_id = picking_type.create(vals={
                'name': _('RMA Receipts'),
                'warehouse_id': warehouse.id,
                'code': 'incoming',
                'sequence_id': in_seq_id.id,
                'default_location_src_id': customer_loc.id,
                'default_location_dest_id': loc_rma.id,
                'sequence': max_sequence + 4,
                'color': color})

        out_type_id = warehouse.rma_out_type_id
        if not out_type_id:
            out_type_id = picking_type.create(vals={
                'name': _('RMA Delivery Orders'),
                'warehouse_id': warehouse.id,
                'code': 'outgoing',
                'sequence_id': out_seq_id.id,
                'return_picking_type_id': in_type_id.id,
                'default_location_src_id': loc_rma.id,
                'default_location_dest_id': supplier_loc.id,
                'sequence': max_sequence + 1,
                'color': color})
            in_type_id.write({'return_picking_type_id': out_type_id.id})

        int_type_id = warehouse.rma_int_type_id
        if not int_type_id:
            int_type_id = picking_type.create(vals={
                'name': _('RMA Internal Transfers'),
                'warehouse_id': warehouse.id,
                'code': 'internal',
                'sequence_id': int_seq_id.id,
                'default_location_src_id': loc_rma.id,
                'default_location_dest_id': loc_rma.id,
                'active': True,
                'sequence': max_sequence + 2,
                'color': color})

        destruction_type_id = warehouse.rma_destruction_type_id
        if not destruction_type_id:
            destruction_type_id = picking_type.create(vals={
                'name': _('Destruction of products'),
                'warehouse_id': warehouse.id,
                'code': 'incoming',
                'sequence_id': destruction_seq_id.id,
                'default_location_src_id': loc_rma.id,
                'default_location_dest_id': loc_loss.id,
                'sequence': max_sequence + 3,
                'color': color})

        # write picking types on WH
        return {
            'rma_in_type_id': in_type_id.id,
            'rma_out_type_id': out_type_id.id,
            'rma_int_type_id': int_type_id.id,
            'rma_destruction_type_id': destruction_type_id.id,
        }

    @api.model
    def create_locations_rma(self, warehouse_id):
        """Create a RMA location for RMA movements that takes place when internal,
        outgoing or incoming pickings are made from/to this location
        """
        vals = {}

        location_obj = self.env['stock.location']
        context_with_inactive = self.env.context.copy()
        context_with_inactive['active_test'] = False

        if not warehouse_id.lot_rma_id:
            loc_vals = {
                'name': _('RMA'),
                'usage': 'internal',
                'location_id': warehouse_id.view_location_id.id,
                'company_id': warehouse_id.company_id.id,
                'active': True,
            }
            location_id = location_obj.with_context(context_with_inactive).\
                create(loc_vals)
            vals['lot_rma_id'] = location_id.id

        if not warehouse_id.loss_loc_id:
            loc_vals.update({
                'name': _('Loss'),
                'usage': 'internal'
            })
            location_id = location_obj.with_context(context_with_inactive).\
                create(loc_vals)
            vals['loss_loc_id'] = location_id.id

        if not warehouse_id.lot_refurbish_id:
            loc_vals.update({
                'name': _('Refurbish'),
                'usage': 'internal'
            })
            location_id = location_obj.with_context(context_with_inactive).\
                create(loc_vals)
            vals['lot_refurbish_id'] = location_id.id

        return vals

    @api.model
    def create(self, vals):
        """Create Locations and picking types for warehouse
        """
        warehouse_id = super(StockWarehouse, self).create(vals=vals)
        new_vals = self.create_locations_rma(warehouse_id)
        warehouse_id.write(vals=new_vals)
        new_vals = self.create_sequences_picking_types(warehouse_id)
        warehouse_id.write(vals=new_vals)
        return warehouse_id
