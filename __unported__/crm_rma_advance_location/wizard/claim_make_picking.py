# -*- coding: utf-8 -*-
#########################################################################
#                                                                       #
#                                                                       #
#########################################################################
#                                                                       #
# crm_claim_rma for OpenERP                                             #
# Copyright (C) 2009-2012  Akretion, Emmanuel Samyn,                    #
#       Benoît GUILLOT <benoit.guillot@akretion.com>                    #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################
from openerp.osv import orm


class claim_make_picking(orm.TransientModel):

    _inherit = 'claim_make_picking.wizard'

    def _get_dest_loc(self, cr, uid, context=None):
        """ Get default destination location """
        loc_id = super(claim_make_picking, self)._get_dest_loc(cr, uid, context=context)
        if context is None:
            context = {}
        warehouse_obj = self.pool.get('stock.warehouse')
        warehouse_id = context.get('warehouse_id')
        if context.get('picking_type') == 'in':
            loc_id = warehouse_obj.read(
                cr, uid,
                warehouse_id,
                ['lot_rma_id'],
                context=context)['lot_rma_id'][0]
        elif context.get('picking_type') == 'loss':
            loc_id = warehouse_obj.read(
                cr, uid,
                warehouse_id,
                ['lot_carrier_loss_id'],
                context=context)['lot_carrier_loss_id'][0]
        return loc_id

    _defaults = {
        'claim_line_dest_location': _get_dest_loc,
    }
