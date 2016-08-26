# -*- coding: utf-8 -*-
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Joel Grand-Guillaume
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import _, api, fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    loss_loc_id = fields.Many2one('stock.location', 'Loss Location')

    lot_refurbish_id = fields.Many2one('stock.location', 'Refurbish Location')

    @api.multi
    def create_locations_rma(self):
        super(StockWarehouse, self).create_locations_rma()

        location_obj = self.env['stock.location']

        for warehouse in self:
            if not warehouse.lot_refurbish_id:
                location_id = location_obj.with_context(
                    active_test=False
                ).create({
                    'name': _('Refurbish'),
                    'usage': 'production',
                    'location_id': warehouse.view_location_id.id,
                    'company_id': warehouse.company_id.id,
                    'active': True,
                })
                warehouse.lot_refurbish_id = location_id

            if not warehouse.loss_loc_id:
                location_id = location_obj.with_context(
                    active_test=False
                ).create({
                    'name': _('Loss'),
                    'usage': 'inventory',
                    'location_id': warehouse.view_location_id.id,
                    'company_id': warehouse.company_id.id,
                    'active': True,
                })
                warehouse.loss_loc_id = location_id
