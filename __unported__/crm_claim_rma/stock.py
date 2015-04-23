# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 credativ ltd.
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume, Ondřej Kuzník
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
from openerp import fields, models


class stock_picking(models.Model):

    _inherit = "stock.picking"

    claim_id = fields.Many2one('crm.claim', 'Claim')


# This part concern the case of a wrong picking out. We need to create a new
# stock_move in a picking already open.
# In order to don't have to confirm the stock_move we override the create and
# confirm it at the creation only for this case
class stock_move(models.Model):

    _inherit = "stock.move"

    def create(self, cr, uid, vals, context=None):
        move_id = super(stock_move, self
                        ).create(cr, uid, vals, context=context)
        move = self.browse(cr, uid, move_id, context=context)
        if move.picking_id and move.picking_id.claim_id:
            picking_code = self.get_code_from_locs(
                cr, uid, move, context=context)

            if picking_code == 'incoming':
                self.write(cr, uid, move_id, {'state': 'confirmed'},
                           context=context)
        return move_id
