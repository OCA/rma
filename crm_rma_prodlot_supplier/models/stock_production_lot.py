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

from openerp import api, fields, models


class StockProductionLot(models.Model):

    _inherit = 'stock.production.lot'

    supplier_id = fields.Many2one('res.partner', string='Supplier',
                                  help="Supplier of good in claim")

    supplier_invoice_line_id = \
        fields.Many2one('account.invoice.line',
                        string='Supplier Invoice Line',
                        help="Supplier invoice with the "
                             "purchase of goods sold to "
                             "customer")

    @api.model
    def default_get(self, fields_list):
        """
        Set partner when product lot is created
        @param fields_list: record values
        @return: return record
        """
        res = super(StockProductionLot, self).default_get(fields_list)

        prodlot_obj = self.env['stock.production.lot']
        transfer_item_id = self._context.get('active_id', False)

        if not transfer_item_id:
            return res

        picking = self.env['stock.transfer_details_items'].\
            browse(transfer_item_id)

        if picking.transfer_id.picking_id.picking_type_id.code != 'incoming':
            return res

        partner_id = picking.transfer_id.picking_id.partner_id

        for move_line in picking.transfer_id.picking_id.move_lines:
            if res.get('product_id') != move_line.product_id.id:
                continue

            lots = prodlot_obj.search([
                ('supplier_invoice_line_id',
                 'in', move_line.purchase_line_id.invoice_lines.mapped('id'))
            ])

            if len(lots) < move_line.purchase_line_id.product_qty:

                for inv_line in move_line.purchase_line_id.invoice_lines:
                    lots = prodlot_obj.\
                        search([('supplier_invoice_line_id',
                                 '=', inv_line.id)])

                    if len(lots) < inv_line.quantity and \
                            inv_line.product_id.id == res.get('product_id'):
                        res.update({'supplier_invoice_line_id': inv_line.id})

        if partner_id:
            res.update({'supplier_id': partner_id.id})
        return res
