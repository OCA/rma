# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2014 Camptocamp SA
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

from openerp.osv import orm, fields
import openerp.addons.decimal_precision as dp


class ProductProduct(orm.Model):
    _inherit = 'product.product'

    def _rma_product_available(self, cr, uid, ids, field_names=None, arg=False,
                               context=None):
        """ Finds the incoming and outgoing quantity of product for the RMA
        locations.
        """
        if field_names is None:
            field_names = []
        if context is None:
            context = {}
        warehouse_obj = self.pool['stock.warehouse']
        res = {}
        for id in ids:
            res[id] = {}.fromkeys(field_names, 0.0)

        for field in field_names:
            ctx = context.copy()

            warehouse_id = ctx.get('warehouse_id')
            # no dependency on 'sale', the same oddness is done in
            # 'stock' so I kept it here
            if ctx.get('shop') and self.pool.get('sale.shop'):
                shop_obj = self.pool['sale.shop']
                shop_id = ctx['shop']
                warehouse = shop_obj.read(cr, uid, shop_id,
                                          ['warehouse_id'],
                                          context=ctx)
                warehouse_id = warehouse['warehouse_id'][0]

            if warehouse_id:
                rma_id = warehouse_obj.read(cr, uid,
                                            warehouse_id,
                                            ['lot_rma_id'],
                                            context=ctx)['lot_rma_id'][0]
                if rma_id:
                    ctx['location'] = rma_id
            else:
                location_ids = set()
                wids = warehouse_obj.search(cr, uid, [], context=context)
                if not wids:
                    return res
                for wh in warehouse_obj.browse(cr, uid, wids, context=context):
                    if wh.lot_rma_id:
                        location_ids.add(wh.lot_rma_id.id)
                if not location_ids:
                    return res
                ctx['location'] = list(location_ids)

            ctx['compute_child'] = True
            compute = {
                'rma_qty_available': {
                    'states': ('done', ),
                    'what': ('in', 'out')
                },
                'rma_virtual_available': {
                    'states': ('confirmed', 'waiting', 'assigned', 'done'),
                    'what': ('in', 'out')
                }
            }
            ctx.update(compute[field])
            stock = self.get_product_available(cr, uid, ids, context=ctx)
            for id in ids:
                res[id][field] = stock.get(id, 0.0)
        return res

    _columns = {
        'rma_qty_available': fields.function(
            _rma_product_available,
            type='float',
            multi='rma_qty',
            digits_compute=dp.get_precision('Product Unit of Measure'),
            string='RMA Quantity On Hand'),
        'rma_virtual_available': fields.function(
            _rma_product_available,
            type='float',
            multi='rma_qty',
            digits_compute=dp.get_precision('Product Unit of Measure'),
            string='RMA Forecasted Quantity'),
    }
