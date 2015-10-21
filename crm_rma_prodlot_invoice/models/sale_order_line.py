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
        res = super(SaleOrderLine, self).invoice_line_create()
        for order_line in self:
            prodlot_obj = self.env['stock.production.lot']
            procurements = order_line.procurement_ids

            if not procurements:
                continue

            move_id = self.env['stock.move'].\
                search([('procurement_id', '=',
                         order_line.procurement_ids[0].id)], limit=1)

            if move_id and move_id.quant_ids:
                lot = move_id.quant_ids[0].lot_id

                if lot.invoice_line_id:
                    continue

                for inv_line_id in res:

                    inv_line = self.env['account.invoice.line'].\
                        browse(inv_line_id)

                    lots = prodlot_obj.search([('invoice_line_id', '=',
                                                inv_line.id)])

                    if inv_line.product_id.id == lot.product_id.id and \
                            len(lots) < inv_line.quantity:
                        lot.write({'invoice_line_id': inv_line.id})
        return res
