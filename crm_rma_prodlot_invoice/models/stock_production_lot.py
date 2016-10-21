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

    invoice_line_id = fields.Many2one('account.invoice.line',
                                      string='Customer Invoice Line',
                                      help="Invoice Line Of "
                                      "Product to Customer Invoice")

    @api.model
    def _get_related_count(self, field_id, field_name='invoice_line_id'):
        """Get how many serial/lot number are related to a given field name,
        by default it will search with invoice_line_ids
        :field_id: it's the record itself to be searched by.
        :field_name: field name to search the serial/lot is related with, as
        default value is 'invoice_line_id' (is used most of the time)
        """
        return field_id and len(self.env['stock.production.lot'].search(
            [(field_name, '=', field_id.id)])) or 0
