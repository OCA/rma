# -*- encoding: utf-8 -*-
###############################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://www.vauxoo.com>).
#    All Rights Reserved
# ############ Credits ########################################################
#    Coded by: Yanina Aular <yani@vauxoo.com>
#    Planified by: Yanina Aular <yani@vauxoo.com>
#    Audited by: Moises Lopez <moylop260@vauxoo.com>
#                Nhomar Hernandez <nhomar@vauxoo.com>
###############################################################################
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


class crm_claim(models.Model):

    _inherit = 'crm.claim'

    @api.model
    def get_supplier_and_supplier_invoice(self):
        """
        Return the last line of customer invoice
        based in serial/lot number
        """


        # TODO method for get supplier and supplier invoice

        # If there is a lot number, the product
        # vendor is searched accurately.
        # inv_obj = self.env['account.invoice']
        # invline_obj = self.env['account.invoice.line']
        # lot_obj = self.env['stock.production.lot']

        # # Take all stock moves with outgoing type of operation
        # sm_delivery = self._get_stock_moves_with_code('outgoing')

        # # Get traceability of serial/lot number
        # quant_obj = self.env['stock.quant']
        # quants = quant_obj.search([('lot_id', '=', prodlot_id)])
        # moves = set()
        # for quant in quants:
        #     moves |= {move.id for move in quant.history_ids}

        # # Make intersection between delivery moves and traceability moves
        # # If product was sold just once, moves will be just one id
        # # If product was sold more than once, the list have multiple ids
        # moves &= {sm_d.id for sm_d in sm_delivery}

        # moves = list(moves)
        # # The last move correspond to the last sale
        # moves.sort(reverse=True)
        # moves = self.env['stock.move'].browse(moves)

        # prodlot_id = lot_obj.browse(prodlot_id)

        # # Filter invoices lines by customer invoice lines
        # invoice_client = False
        # invoice_customer = inv_obj.search([('type', '=', 'out_invoice')])
        # invoice_customer = [inv.id for inv in invoice_customer]
        # invline_customer = invline_obj.search([('invoice_id',
        #                                         'in',
        #                                         invoice_customer)])

        # # The move(s) is searched in invoice lines.
        # # It will take the last line of customer invoice
        # for stock_move in moves:
        #     invoice_client = \
        #         invline_customer.search([('move_id',
        #                                   '=',
        #                                   stock_move.id)])
        #     if invoice_client:
        #         return invoice_client.id

        return False



