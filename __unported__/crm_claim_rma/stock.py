# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume
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
from openerp.osv import fields, orm


class stock_picking(orm.Model):

    _inherit = "stock.picking"

    _columns = {
        'claim_id': fields.many2one('crm.claim', 'Claim'),
    }

    def create(self, cr, uid, vals, context=None):
        if ('name' not in vals) or (vals.get('name') == '/'):
            sequence_obj = self.pool.get('ir.sequence')
            if vals['type'] == 'internal':
                seq_obj_name = self._name
            else:
                seq_obj_name = 'stock.picking.' + vals['type']
            vals['name'] = sequence_obj.get(cr, uid, seq_obj_name,
                                            context=context)
        new_id = super(stock_picking, self).create(cr, uid, vals,
                                                   context=context)
        return new_id


class stock_picking_out(orm.Model):

    _inherit = "stock.picking.out"

    _columns = {
        'claim_id': fields.many2one('crm.claim', 'Claim'),
    }


class stock_picking_in(orm.Model):

    _inherit = "stock.picking.in"

    _columns = {
        'claim_id': fields.many2one('crm.claim', 'Claim'),
    }


# This part concern the case of a wrong picking out. We need to create a new
# stock_move in a picking already open.
# In order to don't have to confirm the stock_move we override the create and
# confirm it at the creation only for this case
class stock_move(orm.Model):

    _inherit = "stock.move"

    def create(self, cr, uid, vals, context=None):
        move_id = super(stock_move, self
                        ).create(cr, uid, vals, context=context)
        if vals.get('picking_id'):
            picking_obj = self.pool.get('stock.picking')
            picking = picking_obj.browse(cr, uid, vals['picking_id'],
                                         context=context)
            if picking.claim_id and picking.type == u'in':
                self.write(cr, uid, move_id, {'state': 'confirmed'},
                           context=context)
        return move_id
