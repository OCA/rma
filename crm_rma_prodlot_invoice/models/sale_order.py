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


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.model
    def action_done(self):
        res = super(SaleOrder, self).action_done()
        prodlot_obj = self.env['stock.production.lot']
        for order in self:
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

    @api.multi
    def action_ship_create(self):
        """
        Set stock moves to invoice lines that matches with
        product and product quantity
        """
        res = super(SaleOrder, self).action_ship_create()
        prodlot_obj = self.env['stock.production.lot']
        move_ids = [move for pick in self.picking_ids
                    for move in pick.move_lines]
        invoice_lines = [line for inv in self.invoice_ids
                         for line in inv.invoice_line]

        if invoice_lines and move_ids:
            for inv_line in invoice_lines:
                for mov in move_ids:
                    quants = mov.quant_ids
                    if quants:
                        lot_ids = [qua.lot_id.id for qua in quants]
                        lot_ids = list(set(lot_ids))
                        lots = prodlot_obj.browse(lot_ids)
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
