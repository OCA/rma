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
from openerp.tools.translate import _
from counter import Counter
from openerp.exceptions import except_orm


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

    @api.model
    def create_claim_line(self, claim_id, claim_origine,
                          product_brw, prodlot_id, qty, invline_brw=False):
        return_line = self.env['claim.line']
        return_line.create({
            'claim_id': claim_id,
            'claim_origine': claim_origine,
            'product_id': product_brw and product_brw.id or False,
            'name': product_brw and product_brw.name or invline_brw.name,
            'invoice_line_id': invline_brw and invline_brw.id or
            self.prodlot_2_invoice_line(prodlot_id),
            'product_returned_quantity': qty,
            'prodlot_id': prodlot_id,
            'selected': False,
            'state': 'draft',
            # 'guarantee_limit' :
            # warranty['value']['guarantee_limit'],
            # 'warning' : warranty['value']['warning'],
        })

    # Method to create return lines
    @api.model
    def add_return_lines(self):
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

                    self.create_claim_line(context['active_id'],
                                           claim_origine,
                                           product_brw,
                                           prodlot_id,
                                           qty
                                           )

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
                                   )

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
                         digits=(12, 2))

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
        inv_obj = self.env['account.invoice']
        invline_obj = self.env['account.invoice.line']
        lot_obj = self.env['stock.production.lot']
        sm_obj = self.env['stock.move']

        user_obj = self.env['res.users']
        user = user_obj.browse(self._uid)
        company_id = user.company_id.id
        wh_obj = self.env['stock.warehouse']
        wh_ids = wh_obj.search([('company_id', '=', company_id)])
        if not wh_ids:
            raise except_orm(
                _('Error!'),
                _('There is no warehouse for the current user\'s company.'))

        picking_out = [wh.out_type_id.id for wh in wh_ids]

        # Take all stock moves with outgoing type of operation
        # Get traceability of serial/lot number
        # Make intersection between delivery moves and traceability moves
        # If product was sold just once, moves will be just one id
        # If product was sold more than once, the list have multiple ids
        sm_all = sm_obj.search([('quant_ids.lot_id', '=', prodlot_id),
                                ('picking_id.picking_type_id',
                                 'in', picking_out)])

        moves = [sm.id for sm in sm_all]

        # # Take all stock moves with outgoing type of operation
        # sm_delivery = claim_obj._get_stock_moves_with_code('outgoing')

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

    lines_list_id = fields.Many2many('account.invoice.line',
                                     'account_invoice_line_returned_wizard',
                                     'wizard_id',
                                     'invoice_line_id',
                                     string='Invoice Lines selected',
                                     help='Field used to show the current '
                                          'status of the invoice lines '
                                          'loaded')

    lines_id = fields.Many2many('account.invoice.line',
                                string='Invoice Lines to Select',
                                help='Field used to load the ids of '
                                     'invoice lines in invoices writed')

    scan_data = fields.Text('Products',
                            help='Field used to load and show the '
                            'products')

    scaned_data = fields.Text('Products',
                              help='Field used to load the ids of '
                              'products loaded')

    current_status = fields.Text('Status',
                                 help='Field used to show the current '
                                 'status of the product '
                                 'loaded(Name and quantity)')

    @api.multi
    def get_metasearch_view_brw(self):
        """
        @return: view with metasearch field
        """
        view_id = self.env.\
            ref('crm_rma_lot_mass_return.view_enter_product')
        return view_id

    @api.multi
    def render_metasearch_view(self):
        """
        Render wizard view with metasearch field
        """
        view = self.get_metasearch_view_brw()
        if view:
            return {
                'name': _('Search Product'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'returned_lines_from_serial.wizard',
                'view_id': view.id,
                'views': [(view.id, 'form')],
                'target': 'new',
                'res_id': self.ids[0],
            }

    @api.multi
    def onchange_load_products(self, input_data, lines_list_id, context=None):
        context = context or None
        invoice_obj = self.env['account.invoice']
        invoice_line_obj = self.env['account.invoice.line']
        new_pro = ''
        for np in input_data and input_data.split('\n') or []:
            if '*' in np:
                comput = np.split('*')
                if comput[1].isdigit():
                    new_pro = new_pro + int(comput[1])*(comput[0]+'\n')
                else:
                    new_pro = new_pro + np + '\n'
            else:
                new_pro = np.strip() and \
                    (new_pro + np.strip() + '\n') or new_pro
        prod = Counter(input_data and new_pro.split('\n') or [])
        mes = ''
        ids_data = ''
        all_prod = {}
        line_ids = []
        for product in prod or []:
            if product:
                invoices = invoice_obj.search([('number', '=', product)])

                element_searched = False
                if invoices:
                    invoice_lines = [inv for inv in invoices.invoice_line]
                    line_new_ids = [line.id for line in invoice_lines]
                    line_ids = list(set(line_ids + line_new_ids))
                    element_searched = invoice_line_obj.browse(line_ids)
                else:
                    invoice_line_move_id = self.prodlot_2_invoice_line(product)
                    if invoice_line_move_id:
                        element_searched = invoice_line_obj.\
                            browse(invoice_line_move_id)

                    for item in element_searched:
                        item_name = item.product_id \
                            and item.product_id.name or item.name
                        line_id = '{pid}+{pname}'.format(pid=item.id,
                                                            pname=item_name)
                        if line_id in all_prod:
                            all_prod.\
                                update({line_id: all_prod[line_id] +
                                        prod[product]})
                        else:
                            all_prod.update({line_id: prod[product]})

                if not element_searched:
                    return {'warning':
                            {'message': _('''The product or invoice {produ} \
                                                was not found
                                            '''.format(produ=product.
                                                       encode('utf-8',
                                                              'ignore')
                                                       ))},
                            'value':
                            {'scan_data': '\n'.join(
                                input_data.split('\n')[0:-1])}}
        for line in all_prod:
            name = line.split('+')
            mes = mes + '{0} \t {1}\n'.format(name[1],
                                              all_prod[line])
            ids_data = ids_data + '{pid}\n'.format(pid=name[0])*all_prod[line]

        res = {'value': {'lines_id': [(6, 0, line_ids)],
                         'current_status': mes,
                         'scaned_data': ids_data,
                         },
               'domain': {'lines_list_id': [('id', 'in', line_ids)]}
               }
        return res

    @api.multi
    def add_claim_lines(self):
        context = self._context
        invline_obj = self.env['account.invoice.line']
        inv_recs = []
        if self.scaned_data:
            inv_recs += [invline_obj.browse(int(inv_id))
                         for inv_id in self.scaned_data.strip().split('\n')]
        if self.lines_list_id:
            inv_recs += self.lines_list_id

        for inv_brw in inv_recs:

            product_brw = inv_brw.product_id
            if inv_brw.move_id:
                prodlot_id = inv_brw.move_id.quant_ids[0].lot_id.id
            else:
                prodlot_id = False

            self.create_claim_line(context.get('active_id'),
                                   'none',
                                   product_brw,
                                   prodlot_id, 1, inv_brw)

        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def change_list(self, lines):
        res = {'value': {'lines_list_id': lines,
                         }
               }
        return res
