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

from openerp import api, models


class StockTransferDetails(models.TransientModel):

    _inherit = 'stock.transfer_details'

    @api.one
    def do_detailed_transfer(self):
        """
        When incoming type transfer are made and stock move have serial/lot
        number, the supplier is assigned to the serial/lot number taken from
        picking.
        @return: do_detailed_transfer boolean results
        """
        stock_prod = self.env['stock.production.lot']
        stock_picking = self.env['stock.picking']
        picking_brw = stock_picking.browse(self.picking_id.id)
        if picking_brw.picking_type_id.code == 'incoming':
            for lstits in [self.item_ids, self.packop_ids]:
                for prod in lstits:
                    if prod.lot_id:
                        stock_prod_brw = stock_prod.browse(prod.lot_id.id)
                        if not stock_prod_brw.supplier_id:
                            stock_prod_brw.write({'supplier_id':
                                                  picking_brw.partner_id.id})
        return super(StockTransferDetails, self).do_detailed_transfer()
