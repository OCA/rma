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


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.one
    @api.multi
    def action_ship_create(self):
        res = super(SaleOrder, self).action_ship_create()
        move_ids = [move for pick in self.picking_ids
                    for move in pick.move_lines]
        invoice_line = self.invoice_ids.invoice_line
        if invoice_line:
            for inv_line in invoice_line:
                for mov in move_ids:
                    if inv_line.product_id.id == mov.product_id.id and \
                        inv_line.quantity == mov.product_qty and \
                            not inv_line.move_id:
                        inv_line.write({'move_id': mov.id})
                        move_ids.remove(mov)
                    elif inv_line.move_id.id == mov.id:
                        move_ids.remove(mov)
        return res
