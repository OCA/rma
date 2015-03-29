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

from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp
from openerp.tools.float_utils import float_round


class ProductProduct(osv.Model):
    _inherit = 'product.product'

    def _rma_product_available(self, cr, uid, ids, field_names=None, arg=False,
                               context=None):
        """ Finds the incoming and outgoing quantity of product for the RMA
        locations.
        """
        res = {}
        context = context or {}

        warehouse_id = context.get('warehouse_id')
        warehouse_obj = self.pool.get('stock.warehouse')
        # no dependency on 'sale', the same oddness is done in
        # 'stock' so I kept it here
        ctx = context.copy()

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

        field_names = field_names or []

        domain_products = [('product_id', 'in', ids)]
        domain_quant, domain_move_in, domain_move_out = self._get_domain_locations(cr, uid, ids, context=ctx)
        domain_move_in += self._get_domain_dates(cr, uid, ids, context=ctx) + [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_products
        domain_move_out += self._get_domain_dates(cr, uid, ids, context=ctx) + [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_products
        domain_quant += domain_products
        if context.get('lot_rma_id'):
            if context.get('lot_rma_id'):
                domain_quant.append(('lot_rma_id', '=', context['lot_rma_id']))
            moves_in = []
            moves_out = []
        else:
            moves_in = self.pool.get('stock.move').read_group(cr, uid, domain_move_in, ['product_id', 'product_qty'], ['product_id'], context=ctx)
            moves_out = self.pool.get('stock.move').read_group(cr, uid, domain_move_out, ['product_id', 'product_qty'], ['product_id'], context=ctx)
        quants = self.pool.get('stock.quant').read_group(cr, uid, domain_quant, ['product_id', 'qty'], ['product_id'], context=ctx)
        quants = dict(map(lambda x: (x['product_id'][0], x['qty']), quants))

        moves_in = dict(map(lambda x: (x['product_id'][0], x['product_qty']), moves_in))
        moves_out = dict(map(lambda x: (x['product_id'][0], x['product_qty']), moves_out))
        res = {}
        for product in self.browse(cr, uid, ids, context=context):
            id = product.id
            rma_qty_available = float_round(quants.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            rma_virtual_available = float_round(quants.get(id, 0.0) + moves_in.get(id, 0.0) - moves_out.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            res[id] = {
                'rma_qty_available' : rma_qty_available,
                'rma_virtual_available' : rma_virtual_available,
            }
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


class ProductTemplate(osv.Model):
    _inherit = 'product.template'

    def _rma_product_available(self, cr, uid, ids, name, arg, context=None):
        res = dict.fromkeys(ids, 0)
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id] = {
                "rma_qty_available": sum([p.rma_qty_available for p in product.product_variant_ids]),
                "rma_virtual_available": sum([p.rma_virtual_available for p in product.product_variant_ids]),
            }
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
