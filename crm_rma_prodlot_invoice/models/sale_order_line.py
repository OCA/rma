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

    @api.model
    def _prepare_order_line_invoice_line(self, line, account_id=False):
        """
        @param cur: A database cursor
        @param uid: ID of the user currently logged in
        @param line: sale order line browse
        """
        res = super(SaleOrderLine, self).\
            _prepare_order_line_invoice_line(line, account_id=account_id)
        sm_obj = self.env['stock.move']
        if line.procurement_ids:
            sm_id = sm_obj.search([('procurement_id', '=',
                                    line.procurement_ids[0].id)], limit=1)
            if sm_id:
                res['move_id'] = sm_id and sm_id.id or False
        return res
