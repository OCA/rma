# -*- coding: utf-8 -*-
#########################################################################
#                                                                       #
#                                                                       #
#########################################################################
#                                                                       #
# Copyright (C) 2009-2011  Akretion, Raphaël Valyi, Sébastien Beau, 	#
# Emmanuel Samyn, Benoît Guillot                                        #
#                                                                       #
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

from osv import fields, osv

class stock_picking(osv.osv):

    _inherit = "stock.picking"
    

    _columns = {
        'claim_id': fields.many2one('crm.claim', 'Claim'),
        'claim_picking': fields.boolean('Picking from Claim'),
    }

class stock_warehouse(osv.osv):

    _inherit = "stock.warehouse"
    

    _columns = {
        'lot_rma_id': fields.many2one('stock.location', 'Location RMA'),
        'lot_carrier_loss_id': fields.many2one('stock.location', 'Location Carrier Loss'),
        'lot_breakage_loss_id': fields.many2one('stock.location', 'Location Breakage Loss'),
        'lot_refurbish_id': fields.many2one('stock.location', 'Location Refurbish'),
    }

#This part concern the case of a wrong picking out. We need to create a new stock_move in a micking already open.
#In order to don't have to confirm the stock_move we override the create and confirm it at the creation only for this case

class stock_move(osv.osv):
    
    _inherit = "stock.move"

    def create(self, cr, uid, vals, context=None):
        move_id = super(stock_move, self).create(cr, uid, vals, context=context)
        picking = self.pool.get('stock.picking').browse(cr, uid, vals['picking_id'], context=context)
        if picking.claim_picking and picking.type == u'in':
            move = self.write(cr, uid, move_id, {'state': 'confirmed'}, context=context)
        return move_id