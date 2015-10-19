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

    @api.multi
    def action_done(self):
        """
        Set stock moves to invoice lines that matches with
        product and product quantity when sale order is done
        """
        return self.set_lot_invoice_line(self, 'action_done')

    @api.multi
    def action_ship_create(self):
        """
        Set stock moves to invoice lines that matches with
        product and product quantity when delivery is created
        """
        return self.set_lot_invoice_line(self, 'action_ship_create')

    def set_lot_invoice_line(self, record_set, method=False):
        res = getattr(super(SaleOrder, self), method)() if method else False
        for order_id in record_set:
            move_ids = order_id.mapped('picking_ids.move_lines')
            invoice_lines = order_id.mapped('invoice_ids.invoice_line')

            if not invoice_lines or not move_ids:
                continue

            for inv_line in invoice_lines:
                qty_lots_with_inv_line = len(self.env['stock.production.lot'].
                                             search([('invoice_line_id', '=',
                                                      inv_line.id)]))
                for move_id in move_ids:
                    lots = move_id.mapped('quant_ids.lot_id')
                    for lot in lots:
                        if not lot.invoice_line_id and \
                                inv_line.product_id.id == \
                                lot.product_id.id and \
                                qty_lots_with_inv_line < inv_line.quantity:
                            lot.write({'invoice_line_id': inv_line.id})
        return res
