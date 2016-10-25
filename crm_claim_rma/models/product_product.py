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

from openerp import api, fields, models
import openerp.addons.decimal_precision as dp
from openerp.tools.float_utils import float_round
from openerp.tools.safe_eval import safe_eval


class ProductProduct(models.Model):

    _inherit = 'product.product'

    rma_qty_available = fields.Float(
        compute='_compute_rma_product_available',
        digits_compute=dp.get_precision('Product Unit of Measure'),
        search='_search_rma_product_quantity',
        string='RMA Quantity On Hand')

    rma_virtual_available = fields.Float(
        compute='_compute_rma_product_available',
        digits_compute=dp.get_precision('Product Unit of Measure'),
        search='_search_rma_product_quantity',
        string='RMA Forecasted Quantity')

    @api.model
    def _get_products_for_rma(self):
        product_ids = self.search([]) or []
        return product_ids

    def _search_rma_product_quantity(self, operator, value):
        res = []
        # to prevent sql injections
        assert operator in ('<', '>', '=', '!=', '<=', '>='),\
            'Invalid domain operator'
        assert isinstance(value, (float, int)), 'Invalid domain right operand'

        if operator == '=':
            operator = '=='

        ids = []
        product_ids = self._get_products_for_rma()
        for element in product_ids:
            localdict = {'virtual': element.rma_virtual_available,
                         'qty': element.rma_qty_available,
                         'value': value}
            if safe_eval('qty %s value or virtual %s value' %
                         (operator, operator), localdict):
                ids.append(element.id)
        res.append(('id', 'in', ids))
        return res

    @api.multi
    def _compute_rma_product_available(self):
        """Finds the incoming and outgoing quantity of product for the RMA
        locations.
        """
        context = self.env.context
        warehouse_id = context.get('warehouse_id')
        ctx = context.copy()
        location_ids = set()
        product_ids = self._get_products_for_rma()
        for product in product_ids:
            if warehouse_id and warehouse_id.lot_rma_id:
                location_ids.add(warehouse_id.lot_rma_id.id)
            else:
                wh_ids = self.env['stock.warehouse'].search([])
                for warehouse_id in wh_ids.filtered(lambda r: r.lot_rma_id):
                    location_ids.add(warehouse_id.lot_rma_id.id)

            ctx['location'] = list(location_ids)

            domain_products = [('product_id', 'in', [product.id])]
            domain_quant, domain_move_in, domain_move_out = \
                product.with_context(ctx)._get_domain_locations()
            domain_move_in += product.with_context(ctx)._get_domain_dates() + \
                [('state', 'not in', ('done', 'cancel', 'draft'))] + \
                domain_products
            domain_move_out += product.with_context(ctx).\
                _get_domain_dates() + \
                [('state', 'not in', ('done', 'cancel', 'draft'))] + \
                domain_products
            domain_quant += domain_products
            moves_in = []
            moves_out = []
            lot_id = context.get('lot_id')
            if lot_id:
                domain_quant.append(('lot_id', '=', lot_id))
            else:
                moves_in = self.env['stock.move'].\
                    with_context(ctx).read_group(domain_move_in,
                                                 ['product_id', 'product_qty'],
                                                 ['product_id'])
                moves_out = self.env['stock.move'].\
                    with_context(ctx).read_group(domain_move_out,
                                                 ['product_id', 'product_qty'],
                                                 ['product_id'])
            quants = self.env['stock.quant'].with_context(ctx).read_group(
                domain_quant, ['product_id', 'qty'], ['product_id'])
            quants = dict([(item.get('product_id')[0],
                            item.get('qty')) for item in quants])
            moves_in = dict([(item.get('product_id')[0],
                              item.get('product_qty')) for item in moves_in])
            moves_out = dict([(item.get('product_id')[0],
                               item.get('product_qty')) for item in moves_out])
            product.rma_qty_available = \
                float_round(quants.get(product.id, 0.0),
                            precision_rounding=product.uom_id.rounding)
            product.rma_virtual_available = \
                float_round(quants.get(product.id, 0.0) +
                            moves_in.get(product.id, 0.0) -
                            moves_out.get(product.id, 0.0),
                            precision_rounding=product.uom_id.rounding)
