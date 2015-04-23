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
                    prodlot_id = eval("result.prodlot_id_" + str(num) + ".id")
                if prodlot_id:
                    product_id = \
                        self.get_product_id(prodlot_id)
                    product_brw = product_obj.browse(product_id)
                    claim_origine = eval("result.claim_" + str(num))
                    qty = eval("result.qty_" + str(num))
                    return_line.create({
                        'claim_id': context['active_id'],
                        'claim_origine': claim_origine,
                        'product_id': product_brw.id,
                        'name': product_brw.name,
                        # 'invoice_id' : self.prodlot_2_invoice(
                        #     cr, uid, [prodlot_id],
                        #     [product_id]),
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

    # def prodlot_2_invoice(self, cr, uid, prodlot_id, product_id):
    #     # get stock_move_ids
    #     # stock_move_ids = self.pool.get('stock.move').search(
    #     #     cr, uid, [('prodlot_id', 'in', prodlot_id)])
    #     # if 1 id
    #         # (get stock picking (filter on out ?))
    #         # get invoice_ids from stock_move_id where
    #         # invoice.line.product = prodlot_product and
    #         # invoice customer = claim_partner
    #         # if 1 id
    #             # return invoice_id
    #         # else
    #     # else : move_in / move_out ; 1 move per order line so if many order
    #     # lines with same lot, ...

    #     # return set(self.stock_move_2_invoice(cr, uid, stock_move_ids))
    #     return True

    # def stock_move_2_invoice(self, cr, uid, stock_move_ids):
    #     inv_line_ids = []
    #     res = self.pool.get('stock.move').read(
    #         cr, uid, stock_move_ids, ['sale_line_id'])
    #     sale_line_ids = [
    #         x['sale_line_id'][0] for x in res if x['sale_line_id']]
    #     if not sale_line_ids:
    #         return []
    #     sql_base = "select invoice_id from "
    #                "sale_order_line_invoice_rel where \
    #      order_line_id in ("
    #     cr.execute(sql_base + ','.join(
    #         [str(item) for item in sale_line_ids])+')')
    #     res = cr.fetchall()
    #     for iii in res:
    #         for jjj in iii:
    #             inv_line_ids.append(jjj)

    #     res = self.pool.get('account.invoice.line').read(
    #         cr, uid, inv_line_ids, ['invoice_id'])
    #     return [x['invoice_id'][0] for x in res if x['invoice_id']]
