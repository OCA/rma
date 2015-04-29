# -*- encoding: utf-8 -*-
# ##############################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://www.vauxoo.com>).
#    All Rights Reserved
# ############ Credits ########################################################
#    Coded by: Yanina Aular <yani@vauxoo.com>
#    Planified by: Yanina Aular <yani@vauxoo.com>
#    Audited by: Moises Lopez <moylop260@vauxoo.com>
#                Nhomar Hernandez <nhomar@vauxoo.com>
# ##############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from openerp import models, fields, api


class claim_line(models.Model):

    _inherit = 'claim.line'

    @api.multi
    @api.one
    @api.depends('prodlot_id')
    def _get_supplier_and_supplier_invoice(self):

        claim_obj = self.env['crm.claim']
        inv_obj = self.env['account.invoice']
        invline_obj = self.env['account.invoice.line']

        if self.prodlot_id:

            self.supplier_id = self.prodlot_id.supplier_id.id

            # Take all stock moves with incoming type of operation
            sm_receipts = claim_obj._get_stock_moves_with_code()

            # Get traceability of serial/lot number
            quant_obj = self.env['stock.quant']
            quants = quant_obj.search([('lot_id', '=', self.prodlot_id.id)])
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
            invoice_supplier = inv_obj.search([('type', '=', 'in_invoice')])
            invoice_supplier = [inv.id for inv in invoice_supplier]
            invline_supplier = invline_obj.search([('invoice_id',
                                                    'in',
                                                    invoice_supplier),
                                                   ('product_id',
                                                    '=',
                                                    self.prodlot_id.
                                                    product_id.id)])

            # The move(s) is searched in invoice lines.
            # It will take the first line of supplier invoice
            for stock_move in moves:
                if stock_move.purchase_line_id:
                    invoice_ids = stock_move.purchase_line_id.\
                        order_id.invoice_ids
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

    supplier_id = fields.Many2one('res.partner', string='Supplier',
                                  compute='_get_supplier_and_supplier_invoice',
                                  store=True,
                                  help="Supplier of good in claim")

    supplier_invoice_id = \
        fields.Many2one('account.invoice',
                        string='Supplier Invoice',
                        compute='_get_supplier_and_supplier_invoice',
                        store=True,
                        help="Supplier invoice with the "
                             "purchase of goods sold to "
                             "customer")
