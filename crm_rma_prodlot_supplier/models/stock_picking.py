# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Author: Yanina Aular
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


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    @api.multi
    def action_invoice_create(self, journal_id,
                              group=False, type='out_invoice'):
        invoices = super(StockPicking, self).\
            action_invoice_create(journal_id=journal_id,
                                  group=group,
                                  type=type)
        if type == 'in_invoice':
            prodlot_obj = self.env['stock.production.lot']
            for picking in self:
                for move in picking.move_lines:
                    if move and move.quant_ids:
                        lot = move.quant_ids[0].lot_id
                        if lot.supplier_invoice_line_id:
                            continue
                        for inv_id in invoices:
                            for inv_line in self.env['account.invoice'].\
                                    browse(inv_id).invoice_line:
                                lots = prodlot_obj.\
                                    search([('supplier_invoice_line_id',
                                             '=',
                                             inv_line.id)])
                                if inv_line.product_id.id == \
                                        lot.product_id.id and \
                                        len(lots) < inv_line.quantity:
                                    lot.write({'supplier_invoice_line_id':
                                               inv_line.id})
        return invoices
