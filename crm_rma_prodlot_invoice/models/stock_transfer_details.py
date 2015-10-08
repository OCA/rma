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

    @api.multi
    def do_detailed_transfer(self):
        """
        When incoming type transfer are made and stock move have serial/lot
        number, the supplier is assigned to the serial/lot number taken from
        picking.
        @return: do_detailed_transfer boolean results
        """
        res = super(StockTransferDetails, self).do_detailed_transfer()

        picking_ids = self.env['stock.picking'].browse(self.picking_id.id)
        order = picking_ids.sale_id
        move_ids = order.mapped('picking_ids.move_lines')
        invoice_lines = order.mapped('invoice_ids.invoice_line')

        if not invoice_lines or not move_ids:
            return res

        for inv_line in invoice_lines:
            for mov in move_ids:

                quants = mov.quant_ids
                if not quants:
                    continue

                lots = list(set([qua.lot_id for qua in quants]))
                for lot in lots:

                    lots_with_inv_line = self.env['stock.production.lot'].\
                        search([('invoice_line_id', '=',
                                 inv_line.id)])

                    if not lot.invoice_line_id and \
                            inv_line.product_id.id == lot.product_id.id and \
                            len(lots_with_inv_line) < inv_line.quantity:
                        lot.write({'invoice_line_id': inv_line.id})
        return res
