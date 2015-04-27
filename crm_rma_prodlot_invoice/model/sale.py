# -*- encoding: utf-8 -*-
###############################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://www.vauxoo.com>).
#    All Rights Reserved
# ############ Credits #######################################################
#    Coded by: Yanina Aular <yani@vauxoo.com>
#    Planified by: Yanina Aular <yani@vauxoo.com>
#    Audited by: Nhomar Hernandez <nhomar@vauxoo.com>
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

from openerp.osv import osv


class sale_order(osv.osv):
    _inherit = 'sale.order'

    def action_ship_create(self, cr, uid, ids, context=None):
        res = super(sale_order, self).action_ship_create(cr,
                                                         uid,
                                                         ids,
                                                         context=context)
        invline_obj = self.pool.get('account.invoice.line')
        move_id = self.browse(cr, uid, ids).picking_ids.move_lines
        invoice_line = self.browse(cr, uid, ids).invoice_ids.invoice_line
        move_id = [move for move in move_id]
        if invoice_line:
            for inv_line in invoice_line:
                for mov in move_id:
                    if inv_line.product_id.id == mov.product_id.id and \
                        inv_line.quantity == mov.product_qty and \
                            not inv_line.move_id:
                        invline_obj.write(cr, uid,
                                          [inv_line.id],
                                          {'move_id': mov.id})
                        move_id.remove(mov)
                    elif inv_line.move_id:
                        move_id.remove(mov)

        return res


class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    def _prepare_order_line_invoice_line(self, cur, uid, line,
                                         account_id=False, context=None):
        """
        @param cur: A database cursor
        @param uid: ID of the user currently logged in
        @param line: sale order line browse
        """
        res = \
            super(sale_order_line,
                  self)._prepare_order_line_invoice_line(cur,
                                                         uid,
                                                         line,
                                                         account_id=account_id,
                                                         context=context)
        sm_obj = self.pool.get('stock.move')
        if line.procurement_ids:
            sm_id = sm_obj.search(cur, uid,
                                  [('procurement_id', '=',
                                    line.procurement_ids[0].id)],
                                  context=context)

            if sm_id:
                res['move_id'] = sm_id if isinstance(
                    sm_id, (int, long)) else sm_id[0]
        return res
