# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Author: Yanina Aular, Osval Reyes
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

from openerp import api, fields, models


class StockProductionLot(models.Model):

    _inherit = 'stock.production.lot'

    supplier_id = fields.Many2one('res.partner', string='Supplier',
                                  help="Supplier of good in claim")

    @api.model
    def default_get(self, fields_list):
        """
        Set partner when product lot is created
        @param fields_list: record values
        @return: return record
        """
        res = super(StockProductionLot, self).default_get(fields_list)
        transfer_item_id = self._context.get('active_id', False)
        if transfer_item_id:
            picking = self.env['stock.transfer_details_items'].\
                browse(transfer_item_id)
            if picking.transfer_id.picking_id.\
                    picking_type_id.code == 'incoming':
                partner_id = picking.transfer_id.picking_id.partner_id
                if partner_id:
                    res.update({'supplier_id': partner_id.id})
        return res
