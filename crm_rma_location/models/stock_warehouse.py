# -*- coding: utf-8 -*-
# © 2013 Camptocamp
# © 2015 Osval Reyes, Yanina Aular, Vauxoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import _, api, fields, models


class StockWarehouse(models.Model):

    _inherit = "stock.warehouse"

    lot_rma_id = fields.Many2one('stock.location', 'RMA Location')
    rma_out_type_id = fields.Many2one('stock.picking.type', 'RMA Out Type')
    rma_in_type_id = fields.Many2one('stock.picking.type', 'RMA In Type')
    rma_int_type_id = fields.Many2one('stock.picking.type',
                                      'RMA Internal Type')

    def compute_next_color(self):
        """
        Choose the next available color for
        the picking types of this warehouse
        """
        available_colors = [c % 9 for c in range(3, 12)]
        all_used_colors = self.env['stock.picking.type'].\
            search_read([('warehouse_id', '!=', False),
                         ('color', '!=', False)],
                        ['color'], order='color')
        for col in all_used_colors:
            if col['color'] in available_colors:
                available_colors.remove(col['color'])

        return available_colors[0] if available_colors else 0

    def create_sequence(self, name, prefix, padding):
        self.ensure_one()
        return self.env['ir.sequence'].sudo().\
            create(values={
                'name': self.name + name,
                'prefix': self.code + prefix,
                'padding': padding,
                'company_id': self.company_id.id
            })

    @api.multi
    def create_sequences_picking_types(self):
        """
        Takes care of create picking types for internal,
        incoming and outgoing RMA
        """
        picking_type_model = self.env['stock.picking.type']

        for warehouse in self:
            # create new sequences
            if not warehouse.rma_in_type_id:
                in_seq_id = warehouse.create_sequence(
                    _(' Sequence in'), '/RMA/IN/', 5
                )

            if not warehouse.rma_out_type_id:
                out_seq_id = warehouse.create_sequence(
                    _(' Sequence out'), '/RMA/OUT/', 5
                )

            if not warehouse.rma_int_type_id:
                int_seq_id = warehouse.create_sequence(
                    _(' Sequence internal'), '/RMA/INT/', 5
                )

            wh_stock_loc = warehouse.lot_rma_id

            # fetch customer and supplier locations, for references
            customer_loc, supplier_loc = self._get_partner_locations()

            color = self.compute_next_color()

            # order the picking types with a sequence
            # allowing to have the following suit for
            # each warehouse: reception, internal, pick, pack, ship.
            max_sequence = picking_type_model.search_read(
                [], ['sequence'], order='sequence desc'
            )
            max_sequence = max_sequence and max_sequence[0]['sequence'] or 0

            in_type_id = warehouse.rma_in_type_id
            if not in_type_id:
                in_type_id = picking_type_model.create(vals={
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
                out_type_id = picking_type_model.create(vals={
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
                int_type_id = picking_type_model.create(vals={
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
            warehouse.write({
                'rma_in_type_id': in_type_id.id,
                'rma_out_type_id': out_type_id.id,
                'rma_int_type_id': int_type_id.id,
            })

    @api.multi
    def create_locations_rma(self):
        """
        Create a RMA location for RMA movements that takes place when internal,
        outgoing or incoming pickings are made from/to this location
        """
        location_obj = self.env['stock.location']

        for warehouse in self:
            if not warehouse.lot_rma_id:
                location_id = location_obj.with_context(
                    active_test=False
                ).create({
                    'name': _('RMA'),
                    'usage': 'internal',
                    'location_id': warehouse.view_location_id.id,
                    'company_id': warehouse.company_id.id,
                    'active': True,
                })
                warehouse.lot_rma_id = location_id

    @api.model
    def create(self, vals):
        """
        Create Locations and picking types for warehouse
        """
        warehouse = super(StockWarehouse, self).create(vals=vals)
        warehouse.create_locations_rma()
        warehouse.create_sequences_picking_types()
        return warehouse
