# -*- coding: utf-8 -*-
#########################################################################
#                                                                       #
#                                                                       #
#########################################################################
#                                                                       #
# Copyright (C) 2009-2011  Akretion, Emmanuel Samyn                     #
#                                                                       #
# This program is free software: you can redistribute it and/or modify  #
# it under the terms of the GNU General Public License as published by  #
# the Free Software Foundation, either version 3 of the License, or     #
# (at your option) any later version.                                   #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
# GNU General Public License for more details.                          #
#                                                                       #
# You should have received a copy of the GNU General Public License     #
# along with this program.  If not, see <http://www.gnu.org/licenses/>. #
#########################################################################

from openerp import models, fields, api


class returned_lines_from_serial(models.TransientModel):

    _name = 'returned_lines_from_serial.wizard'

    _description = 'Wizard to create product return lines from serial numbers'

    # Get partner from case is set to filter serials
    @api.model
    def _get_default_partner_id(self):
        partner_id = self.env['crm.claim'].browse(
            [self._context['active_id']]).partner_id
        if partner_id:
            return partner_id[0]
        else:
            return partner_id

    @api.model
    def prodlot_2_product(self, prodlot_ids):
        stock_quant_ids = self.env['stock.production.lot'].search(
            [('id', 'in', prodlot_ids)])
        res = [prod.product_id.id for prod
               in stock_quant_ids if prod.product_id]
        return set(res)

    # Method to get the product id from set
    @api.model
    def get_product_id(self, product_set):
        product_id = False
        for product in self.prodlot_2_product([product_set]):
            product_id = product
        return product_id

    # Method to create return lines
    @api.model
    def add_return_lines(self):
        return_line = self.env['claim.line']
        # Refactor code : create 1 "createmethode" called by each if with
        # values as parameters
        product_obj = self.env['product.product']
        context = self._context

        for result in self:
            for num in xrange(1, 6):
                prodlot_id = False
                if result:
                    # deleted by problems in pylint
                    # exec("prodlot_id = result.prodlot_id_"
                    # + str(num) + ".id")
                    if num == 1:
                        prodlot_id = result.prodlot_id_1.id
                    elif num == 2:
                        prodlot_id = result.prodlot_id_2.id
                    elif num == 3:
                        prodlot_id = result.prodlot_id_3.id
                    elif num == 4:
                        prodlot_id = result.prodlot_id_4.id
                    else:
                        prodlot_id = result.prodlot_id_5.id
                if prodlot_id:
                    product_id = \
                        self.get_product_id(prodlot_id)
                    product_brw = product_obj.browse(product_id)
                    qty = 0.0
                    # deleted by problems in pylint
                    # claim_origine = eval("result.claim_" + str(num))
                    # exec("qty = result.qty_" + str(num))
                    if num == 1:
                        qty = result.qty_1
                        claim_origine = result.claim_1
                    elif num == 2:
                        qty = result.qty_2
                        claim_origine = result.claim_2
                    elif num == 3:
                        qty = result.qty_3
                        claim_origine = result.claim_3
                    elif num == 4:
                        qty = result.qty_4
                        claim_origine = result.claim_4
                    else:
                        qty = result.qty_5
                        claim_origine = result.claim_5

                    return_line.create({
                        'claim_id': context['active_id'],
                        'claim_origine': claim_origine,
                        'product_id': product_brw.id,
                        'name': product_brw.name,
                        'invoice_line_id':
                        self.prodlot_2_invoice_line(prodlot_id),
                        # PRODLOT_ID can be in many invoice !!
                        'product_returned_quantity': qty,
                        'prodlot_id': prodlot_id,
                        'selected': False,
                        'state': 'draft',
                        # 'guarantee_limit' :
                        # warranty['value']['guarantee_limit'],
                        # 'warning' : warranty['value']['warning'],
                    })

    # If "Cancel" button pressed
    @api.multi
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}

    # If "Add & new" button pressed
    @api.multi
    def action_add_and_new(self):
        self.add_return_lines()
        return {
            'context': self._context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'returned_lines_from_serial.wizard',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    # If "Add & close" button pressed
    @api.multi
    def action_add_and_close(self):
        self.add_return_lines()
        return {'type': 'ir.actions.act_window_close'}

    prodlot_id_1 = fields.Many2one('stock.production.lot',
                                   'Serial / Lot Number 1',
                                   required=True)

    prodlot_id_2 = fields.Many2one('stock.production.lot',
                                   'Serial / Lot Number 2')

    prodlot_id_3 = fields.Many2one('stock.production.lot',
                                   'Serial / Lot Number 3')

    prodlot_id_4 = fields.Many2one('stock.production.lot',
                                   'Serial / Lot Number 4')

    prodlot_id_5 = fields.Many2one('stock.production.lot',
                                   'Serial / Lot Number 5')

    qty_1 = fields.Float('Quantity 1',
                         default=lambda *a: 1.0,
                         digits=(12, 2), required=True)

    qty_2 = fields.Float('Quantity 2',
                         default=lambda *a: 1.0,
                         digits=(12, 2))

    qty_3 = fields.Float('Quantity 3',
                         default=lambda *a: 1.0,
                         digits=(12, 2))

    qty_4 = fields.Float('Quantity 4',
                         default=lambda *a: 1.0,
                         digits=(12, 2))

    qty_5 = fields.Float('Quantity 5',
                         default=lambda *a: 1.0,
                         digits=(12, 2))

    claim_1 = fields.Selection([('none', 'Not specified'),
                                ('legal', 'Legal retractation'),
                                ('cancellation', 'Order cancellation'),
                                ('damaged', 'Damaged delivered product'),
                                ('error', 'Shipping error'),
                                ('exchange', 'Exchange request'),
                                ('lost', 'Lost during transport'),
                                ('other', 'Other')], 'Claim Subject',
                                                     default=lambda *a: "none",
                                                     required=True,
                                                     help="To describe"
                                                     " the product problem")

    claim_2 = fields.Selection([('none', 'Not specified'),
                                ('legal', 'Legal retractation'),
                                ('cancellation', 'Order cancellation'),
                                ('damaged', 'Damaged delivered product'),
                                ('error', 'Shipping error'),
                                ('exchange', 'Exchange request'),
                                ('lost', 'Lost during transport'),
                                ('other', 'Other')], 'Claim Subject',
                                                     default=lambda *a: "none",
                                                     help="To describe the"
                                                     " line product"
                                                     " problem")

    claim_3 = fields.Selection([('none', 'Not specified'),
                                ('legal', 'Legal retractation'),
                                ('cancellation', 'Order cancellation'),
                                ('damaged', 'Damaged delivered product'),
                                ('error', 'Shipping error'),
                                ('exchange', 'Exchange request'),
                                ('lost', 'Lost during transport'),
                                ('other', 'Other')], 'Claim Subject',
                                                     default=lambda *a: "none",
                                                     help="To describe the"
                                                     " line product"
                                                     " problem")

    claim_4 = fields.Selection([('none', 'Not specified'),
                                ('legal', 'Legal retractation'),
                                ('cancellation', 'Order cancellation'),
                                ('damaged', 'Damaged delivered product'),
                                ('error', 'Shipping error'),
                                ('exchange', 'Exchange request'),
                                ('lost', 'Lost during transport'),
                                ('other', 'Other')], 'Claim Subject',
                                                     default=lambda *a: "none",
                                                     help="To describe the"
                                                     " line product"
                                                     " problem")

    claim_5 = fields.Selection([('none', 'Not specified'),
                                ('legal', 'Legal retractation'),
                                ('cancellation', 'Order cancellation'),
                                ('damaged', 'Damaged delivered product'),
                                ('error', 'Shipping error'),
                                ('exchange', 'Exchange request'),
                                ('lost', 'Lost during transport'),
                                ('other', 'Other')], 'Claim Subject',
                                                     default=lambda *a: "none",
                                                     help="To describe "
                                                     "the line product"
                                                     " problem")

    partner_id = fields.Many2one('res.partner',
                                 'Partner',
                                 default=_get_default_partner_id)


    @api.model
    def prodlot_2_invoice_line(self, prodlot_id):
        """
        Return the last line of customer invoice
        based in serial/lot number
        """
        # If there is a lot number, the product
        # vendor is searched accurately.
        claim_obj = self.env['crm.claim']
        inv_obj = self.env['account.invoice']
        invline_obj = self.env['account.invoice.line']
        lot_obj = self.env['stock.production.lot']

        # Take all stock moves with outgoing type of operation
        sm_delivery = claim_obj._get_stock_moves_with_code('outgoing')

        # Get traceability of serial/lot number
        quant_obj = self.env['stock.quant']
        quants = quant_obj.search([('lot_id', '=', prodlot_id)])
        moves = set()
        for quant in quants:
            moves |= {move.id for move in quant.history_ids}

        # Make intersection between delivery moves and traceability moves
        # If product was sold just once, moves will be just one id
        # If product was sold more than once, the list have multiple ids
        moves &= {sm_d.id for sm_d in sm_delivery}

        moves = list(moves)
        # The last move correspond to the last sale
        moves.sort(reverse=True)
        moves = self.env['stock.move'].browse(moves)

        prodlot_id = lot_obj.browse(prodlot_id)

        # Filter invoices lines by customer invoice lines
        invoice_client = False
        invoice_customer = inv_obj.search([('type', '=', 'out_invoice')])
        invoice_customer = [inv.id for inv in invoice_customer]
        invline_customer = invline_obj.search([('invoice_id',
                                                'in',
                                                invoice_customer)])

        # The move(s) is searched in invoice lines.
        # It will take the last line of customer invoice
        for stock_move in moves:
            invoice_client = \
                invline_customer.search([('move_id',
                                          '=',
                                          stock_move.id)])
            if invoice_client:
                return invoice_client.id

        return False
