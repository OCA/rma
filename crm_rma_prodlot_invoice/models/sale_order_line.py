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


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    @api.multi
    def invoice_line_create(self):
        invoice_lines = super(SaleOrderLine, self).invoice_line_create()
        self._search_serial_number_to_change_from_sale(invoice_lines)
        return invoice_lines

    @api.multi
    def _search_serial_number_to_change_from_sale(self, invoice_lines):
        """ A customer invoice is generated from sale order.

        When a customer invoice is created from a sale order.
        Then, the invoice lines of invoice must be saved in
        the serial/lot number that are involved in the sale
        order.

        The invoice line must match with the same product
        in the serial/lot number and...

        The invoice line record is saved to a maximum of
        invoice_line.quantity lots. Because, by example,
        it makes no sense that 10 serial/lot numbers have
        a invoice line with quantity = 5.

        :param invoice_lines: The invoice lines of sale order
        to be assigned to serial/lot numbers.

        :return: True
        """
        invoice_line_obj = self.env["account.invoice.line"]
        stock_move_obj = self.env["stock.move"]
        invoice_lines_rec = invoice_line_obj.browse(invoice_lines)
        transfer_obj = self.env["stock.transfer_details"]

        for order_line in self:
            procurements = order_line.procurement_ids
            # If there are not procurements, continue
            # with next sale order line
            if not procurements:
                continue
            # Search stock moves related with the
            # procurements
            procurement_ids = procurements.mapped("id")
            move_ids = stock_move_obj.search(
                [('procurement_id', 'in', procurement_ids)])
            # Get the serial/lot number related with moves
            lot_ids = move_ids.mapped("quant_ids.lot_id")
            # Save invoice lines in the serial/lot numbers
            transfer_obj._set_invoice_line_to_serial_numbers(
                lot_ids, invoice_lines_rec, 'invoice_line_id')
        return True
