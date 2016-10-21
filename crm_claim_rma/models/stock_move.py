# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Eezee-It, MONK Software, Vauxoo
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume, Leonardo Donelli,
#            Osval Reyes
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


class StockMove(models.Model):

    _name = 'stock.move'
    _inherit = ['stock.move', 'mail.thread']

    @api.model
    def create(self, vals):
        """In case of a wrong picking out, We need to create a new stock_move
        in a picking already open. To avoid having to confirm the stock_move,
        we override the create and confirm it at the creation only for this
        case.
        """
        move_id = super(StockMove, self).create(vals)
        picking_id = vals.get('picking_id', False)
        if picking_id:
            picking_id = self.env['stock.picking'].browse(picking_id)
            if picking_id.claim_id \
                    and picking_id.picking_type_id.code == 'incoming':
                move_id.write({'state': 'confirmed'})
        return move_id
