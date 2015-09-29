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

from openerp import _, api, fields, models


class StockProductionLot(models.Model):

    _inherit = 'stock.production.lot'

    invoice_line_id = fields.Many2one('account.invoice.line',
                                      string='Invoice Line',
                                      help="Invoice Line Of Product")

    @api.multi
    def name_get(self):
        """
        Overwrite Odoo method like the one for
        stock.production.lot model in the
        rma module.
        """
        res = []
        for lot in self:
            name = _("%s - Lot Number: %s - %s") % \
                (lot.invoice_line_id.invoice_id.number,
                 lot.name or _('No lot number'),
                 lot.invoice_line_id.name)
            res.append((lot.id, name))
        return res


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
        prodlot_obj = self.env['stock.production.lot']
        stock_picking = self.env['stock.picking']
        picking_brw = stock_picking.browse(self.picking_id.id)
        order = picking_brw.sale_id
        move_ids = [move for pick in order.picking_ids
                    for move in pick.move_lines]
        invoice_lines = [line for inv in order.invoice_ids
                         for line in inv.invoice_line]

        if invoice_lines and move_ids:
            for inv_line in invoice_lines:
                for mov in move_ids:
                    quants = mov.quant_ids
                    if quants:
                        lots = list(set([qua.lot_id for qua in quants]))
                        for lot in lots:

                            lots_with_inv_line = prodlot_obj.\
                                search([('invoice_line_id', '=',
                                        inv_line.id)])

                            if not lot.invoice_line_id and \
                                    inv_line.product_id.id == \
                                    lot.product_id.id and \
                                    len(lots_with_inv_line) < \
                                    inv_line.quantity:
                                lot.write({'invoice_line_id': inv_line.id})
        return res
