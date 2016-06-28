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
from openerp.tools.safe_eval import safe_eval


class StockTransferDetails(models.TransientModel):

    _inherit = 'stock.transfer_details'

    @api.multi
    def _set_invoice_line_to_serial_numbers(self, lot_ids, invoice_lines_rec,
                                            field_to_change):

        prodlot_obj = self.env['stock.production.lot']
        for lot in lot_ids:
            # If serial/lot number has invoice line
            # ignoring the process down and continue
            # with the next serial/lot number in the
            # cycle
            string_to_get_field = "lot.%s" % field_to_change
            invoice_line_in_serial = \
                safe_eval(string_to_get_field, {"lot": lot})
            if invoice_line_in_serial:
                continue
            for inv_line in invoice_lines_rec:
                # Search serial/lot numbers with the invoice line
                # for take into consideration the quantity of
                # lots with the invoice line and compared to
                # the quantity of products in the invoice line
                lots_with_inv_line = prodlot_obj.search(
                    [(field_to_change, '=', inv_line.id)])
                # If The product in the serial/lot number is the same
                # that current invoice line and the quantity of
                # serial/lot number with that invoice line is minor
                # that the quantity of product in the invoice line
                # save the invoice line on th serial/lot number.
                # RMA is just for product with UoM = units
                if inv_line.product_id == lot.product_id and \
                        len(lots_with_inv_line) < inv_line.quantity:
                    lot.write({field_to_change: inv_line.id})
        return True

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
            transfer._set_invoice_line_to_serial_numbers(
                lot_ids, invoice_lines_rec, 'invoice_line_id')
        return True

    @api.multi
    def do_detailed_transfer(self):
        """ When incoming type transfer are made and stock move have
        serial/lot number, the supplier is assigned to the serial/lot
        number taken from picking.
        @return: do_detailed_transfer boolean results
        """
        res = super(StockTransferDetails, self).do_detailed_transfer()
        self._search_serial_number_to_change_from_transfer()

        if self.picking_id.picking_type_id.code != 'incoming':
            return res

        # Save supplier_invoice_line_id in the lot numbers
        items_packs_ids = self.item_ids + self.packop_ids
        lot_ids = items_packs_ids.mapped("lot_id")

        for lot_id in lot_ids:
            if not lot_id.supplier_id:
                lot_id.write({
                    'supplier_id': self.picking_id.partner_id.id
                })

            move_lines = self.picking_id.move_lines.filtered(
                lambda move: move.product_id == lot_id.product_id)

            # Save invoice lines in the serial/lot numbers
            invoice_lines_rec = move_lines.mapped(
                'purchase_line_id.invoice_lines')
            # If there are not invoice and move_ids, continue
            # with next transfer
            if not invoice_lines_rec and not move_lines:
                continue
            # Get the serial/lot number related with moves
            lot_ids = move_lines.mapped("quant_ids.lot_id")
            self._set_invoice_line_to_serial_numbers(
                lot_ids, invoice_lines_rec, 'supplier_invoice_line_id')
        return res
