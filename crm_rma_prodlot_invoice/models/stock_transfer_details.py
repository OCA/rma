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
        """ When incoming type transfer are made and stock move have serial/lot
        number, the supplier is assigned to the serial/lot number taken from
        picking.
        @return: do_detailed_transfer boolean results
        """
        res = super(StockTransferDetails, self).do_detailed_transfer()
        self._search_serial_number_to_change_from_transfer()
        return res

    @api.multi
    def _search_serial_number_to_change_from_transfer(self):
        """ A transfer is made from picking order.

        When a transfer is made from a picking order.
        Then, the invoice lines of invoice related with sale order
        must be saved in the serial/lot number that are
        involved in the transfer.

        The invoice line must match with the same product
        in the serial/lot number and...

        The invoice line record is saved to a maximum of
        invoice_line.quantity lots. Because, by example,
        it makes no sense that 10 serial/lot numbers have
        a invoice line with quantity = 5.

        :return: True
        """
        for transfer in self:
            picking = transfer.picking_id
            order = picking.sale_id
            move_ids = order.mapped('picking_ids.move_lines')
            invoice_lines_rec = order.mapped('invoice_ids.invoice_line')
            # If there are not invoice and move_ids, continue
            # with next transfer
            if not invoice_lines_rec and not move_ids:
                continue
            # Get the serial/lot number related with moves
            lot_ids = move_ids.mapped("quant_ids.lot_id")
            # Save invoice lines in the serial/lot numbers
            picking._set_invoice_line_to_serial_numbers(
                lot_ids, invoice_lines_rec, 'invoice_line_id')
        return True
