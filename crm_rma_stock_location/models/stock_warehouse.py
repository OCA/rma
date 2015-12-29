# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Joel Grand-Guillaume
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

    loss_loc_id = fields.Many2one('stock.location', 'Loss Location')

    lot_refurbish_id = fields.Many2one('stock.location', 'Refurbish Location')

    @api.model
    def create_locations_rma(self, wh_id):
        vals = {}

        location_obj = self.env['stock.location']
        context_with_inactive = self.env.context.copy()
        context_with_inactive['active_test'] = False
        wh_loc_id = wh_id.view_location_id.id

        vals_new = super(StockWarehouse, self).create_locations_rma(wh_id)

        loc_vals = {
            'location_id': wh_loc_id,
            'active': True,
        }

        if vals.get('company_id'):
            loc_vals['company_id'] = vals.get('company_id')

        if not wh_id.lot_refurbish_id:
            loc_vals.update({
                'name': _('Refurbish'),
                'usage': 'production'
            })
            location_id = location_obj.with_context(context_with_inactive).\
                create(loc_vals)
            vals['lot_refurbish_id'] = location_id.id

        if not wh_id.loss_loc_id:
            loc_vals.update({
                'name': _('Loss'),
                'usage': 'inventory'
            })
            location_id = location_obj.with_context(context_with_inactive).\
                create(loc_vals)
            vals['loss_loc_id'] = location_id.id

        vals.update(vals_new)
        return vals
