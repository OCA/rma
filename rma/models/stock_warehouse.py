# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, _


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    # This is a strategic field used to create an rma location
    # and rma operation types in existing warehouses when
    # installing this module.
    rma = fields.Boolean(
        'RMA',
        default=True,
        help="RMA related products can be stored in this warehouse.")
    rma_in_type_id = fields.Many2one(
        comodel_name='stock.picking.type',
        string='RMA In Type',
    )
    rma_out_type_id = fields.Many2one(
        comodel_name='stock.picking.type',
        string='RMA Out Type',
    )
    rma_loc_id = fields.Many2one(
        comodel_name='stock.location',
        string='RMA Location',
    )

    def _get_locations_values(self, vals):
        values = super()._get_locations_values(vals)
        values.update({
            'rma_loc_id': {
                'name': 'RMA',
                'active': True,
                'return_location': True,
                'usage': 'internal',
                'company_id': vals.get('company_id', self.company_id.id),
                'location_id': self.view_location_id.id,
            },
        })
        return values

    def _get_sequence_values(self):
        values = super()._get_sequence_values()
        values.update({
            'rma_in_type_id': {
                'name': self.name + ' ' + _('Sequence RMA in'),
                'prefix': self.code + '/RMA/IN/', 'padding': 5,
                'company_id': self.company_id.id,
            },
            'rma_out_type_id': {
                'name': self.name + ' ' + _('Sequence RMA out'),
                'prefix': self.code + '/RMA/OUT/', 'padding': 5,
                'company_id': self.company_id.id,
            },
        })
        return values

    def _update_name_and_code(self, new_name=False, new_code=False):
        for warehouse in self:
            sequence_data = warehouse._get_sequence_values()
            warehouse.rma_in_type_id.sequence_id.write(
                sequence_data['rma_in_type_id'])
            warehouse.rma_out_type_id.sequence_id.write(
                sequence_data['rma_out_type_id'])

    def _get_picking_type_create_values(self, max_sequence):
        data, next_sequence = super()._get_picking_type_create_values(
            max_sequence)
        data.update({
            'rma_in_type_id': {
                'name': _('RMA Receipts'),
                'code': 'incoming',
                'use_create_lots': True,
                'use_existing_lots': False,
                'default_location_src_id': False,
                'default_location_dest_id': self.rma_loc_id.id,
                'sequence': max_sequence + 1,
            },
            'rma_out_type_id': {
                'name': _('RMA Delivery Orders'),
                'code': 'outgoing',
                'use_create_lots': False,
                'use_existing_lots': True,
                'default_location_src_id': self.rma_loc_id.id,
                'default_location_dest_id': False,
                'sequence': max_sequence + 2,
            },
        })
        return data, max_sequence + 3

    def _get_picking_type_update_values(self):
        data = super()._get_picking_type_update_values()
        data.update({
            'rma_in_type_id': {
                'default_location_dest_id': self.rma_loc_id.id,
            },
            'rma_out_type_id': {
                'default_location_src_id': self.rma_loc_id.id,
            },
        })
        return data

    def _create_or_update_sequences_and_picking_types(self):
        data = super()._create_or_update_sequences_and_picking_types()
        stock_picking_type = self.env['stock.picking.type']
        if 'out_type_id' in data:
            rma_out_type = stock_picking_type.browse(data['rma_out_type_id'])
            rma_out_type.write({
                'return_picking_type_id': data.get('rma_in_type_id', False)
            })
        if 'rma_in_type_id' in data:
            rma_in_type = stock_picking_type.browse(data['rma_in_type_id'])
            rma_in_type.write({
                'return_picking_type_id': data.get('rma_out_type_id', False)
            })
        return data
