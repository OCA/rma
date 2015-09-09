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
from openerp import api, fields, models


class ClaimLine(models.Model):

    _inherit = 'claim.line'

    supplier_id = \
        fields.Many2one('res.partner', string='Supplier',
                        compute='_compute_supplier_and_supplier_invoice',
                        store=True,
                        help="Supplier of good in claim")
    supplier_invoice_id = \
        fields.Many2one('account.invoice',
                        string='Supplier Invoice',
                        compute='_compute_supplier_and_supplier_invoice',
                        store=True,
                        help="Supplier invoice with the "
                             "purchase of goods sold to "
                             "customer")

    @api.multi
    @api.one
    @api.depends('prodlot_id')
    def _compute_supplier_and_supplier_invoice(self):

        if self.prodlot_id:

            self.supplier_id = self.prodlot_id.supplier_id.id

            # Take all stock moves with incoming type of operation
            sm_receipts = self.env['crm.claim']._get_stock_moves_with_code()

            # Get traceability of serial/lot number
            quants = self.env['stock.quant'].\
                search([('lot_id', '=', self.prodlot_id.id)])
            moves = set()
            for quant in quants:
                moves |= {move.id for move in quant.history_ids}

            # Make intersection between delivery moves and traceability moves
            # If product was sold just once, moves will be just one id
            # If product was sold more than once, the list have multiple ids
            moves &= {sm_d.id for sm_d in sm_receipts}

            moves = list(moves)
            # The FIRST move correspond to the original sale
            moves.sort()
            moves = self.env['stock.move'].browse(moves)

            # Filter invoices lines by customer invoice lines
            invoice_supplier = False
            invoice_supplier = self.env['account.invoice'].\
                search([('type', '=', 'in_invoice')])
            invoice_supplier = [inv.id for inv in invoice_supplier]
            invline_supplier = self.env['account.invoice.line'].\
                search([('invoice_id', 'in', invoice_supplier),
                        ('product_id', '=', self.prodlot_id.product_id.id)])

            # The move(s) is searched in invoice lines.
            # It will take the first line of supplier invoice
            for stock_move in moves:
                if stock_move.purchase_line_id:
                    invoice_ids = stock_move.purchase_line_id.\
                        order_id.invoice_ids
                    inv_line = False
                    for inv in invoice_ids:
                        inv_line = set(inv.invoice_line) \
                            & set(invline_supplier)
                        inv_line = list(inv_line)
                        if inv_line:
                            invoice_supplier = inv.id
                            break
                    if inv_line:
                        break
            self.supplier_invoice_id = invoice_supplier
