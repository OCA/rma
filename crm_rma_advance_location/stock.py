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

from openerp import models, fields, api, SUPERUSER_ID
from openerp.tools.translate import _


class stock_warehouse(models.Model):

    _inherit = "stock.warehouse"

    lot_carrier_loss_id = fields.Many2one(
        'stock.location',
        'Carrier Loss Location')
    lot_breakage_loss_id = fields.Many2one(
        'stock.location',
        'Breakage Loss Location')
    lot_refurbish_id = fields.Many2one(
        'stock.location',
        'Refurbish Location')

    def init(self, cr):
        for wh_id in self.browse(cr, SUPERUSER_ID,
                                 self.search(cr, SUPERUSER_ID, [])):
            vals = self.create_locations_rma(cr, SUPERUSER_ID, wh_id)
            self.write(cr, SUPERUSER_ID, wh_id.id, vals=vals)

    @api.model
    def create_locations_rma(self, wh_id):
        vals = {}

        location_obj = self.env['stock.location']
        context = self._context
        context_with_inactive = context.copy()
        context_with_inactive['active_test'] = False
        wh_loc_id = wh_id.view_location_id.id

        vals_new = super(stock_warehouse, self).create_locations_rma(wh_id)
        sub_locations = [
            {'name': _('Refurbish'), 'active': True,
             'field': 'lot_refurbish_id'},
            {'name': _('Carrier Loss'), 'active': True,
             'field': 'lot_carrier_loss_id'},
            {'name': _('Breakage Loss'), 'active': True,
             'field': 'lot_breakage_loss_id'},
        ]
        for values in sub_locations:
            if not eval('wh_id.'+values['field']):
                loc_vals = {
                    'name': values['name'],
                    'usage': 'internal',
                    'location_id': wh_loc_id,
                    'active': values['active'],
                }
                if vals.get('company_id'):
                    loc_vals['company_id'] = vals.get('company_id')
                location_id = location_obj.\
                    create(loc_vals, context=context_with_inactive)
                vals[values['field']] = location_id.id
        vals.update(vals_new)
        return vals
