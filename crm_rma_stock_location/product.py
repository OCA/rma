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

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp
from openerp.tools.float_utils import float_round


class ProductProduct(models.Model):

    _inherit = 'product.product'

    @api.one
    @api.depends('rma_qty_available', 'rma_virtual_available')
    def _rma_product_available(self):
        """ Finds the incoming and outgoing quantity of product for the RMA
        locations.
        """
        context = self._context

        warehouse_id = context.get('warehouse_id')
        warehouse_obj = self.env['stock.warehouse']
        # no dependency on 'sale', the same oddness is done in
        # 'stock' so I kept it here
        ctx = context.copy()

        if warehouse_id:
            rma_id = warehouse_obj.read(warehouse_id,
                                        ['lot_rma_id'])['lot_rma_id'][0]
            if rma_id:
                ctx['location'] = rma_id
        else:
            location_ids = set()
            wids = warehouse_obj.search([])
            if not wids:
                return
            for wh in wids:
                if wh.lot_rma_id:
                    location_ids.add(wh.lot_rma_id.id)
            if not location_ids:
                return
            ctx['location'] = list(location_ids)

        domain_products = [('product_id', 'in', [self.id])]
        domain_quant, domain_move_in, domain_move_out = \
            self.with_context(ctx)._get_domain_locations()
        domain_move_in += self.with_context(ctx)._get_domain_dates() + \
            [('state',
              'not in',
              ('done', 'cancel', 'draft'))] + domain_products
        domain_move_out += self.with_context(ctx)._get_domain_dates() + \
            [('state',
              'not in',
              ('done', 'cancel', 'draft'))] + domain_products
        domain_quant += domain_products
        if context.get('lot_rma_id'):
            if context.get('lot_rma_id'):
                domain_quant.append(('lot_rma_id', '=', context['lot_rma_id']))
            moves_in = []
            moves_out = []
        else:
            moves_in = self.env['stock.move'].\
                with_context(ctx).read_group(domain_move_in,
                                             ['product_id',
                                              'product_qty'],
                                             ['product_id'])
            moves_out = self.env['stock.move'].\
                with_context(ctx).read_group(domain_move_out,
                                             ['product_id',
                                              'product_qty'],
                                             ['product_id'])

        quants = self.env['stock.quant'].\
            with_context(ctx).read_group(domain_quant,
                                         ['product_id',
                                          'qty'],
                                         ['product_id'])

        quants = dict([(item.get('product_id')[0],
                        item.get('qty')) for item in quants])

        moves_in = dict([(item.get('product_id')[0],
                          item.get('product_qty')) for item in moves_in])

        moves_out = dict([(item.get('product_id')[0],
                           item.get('product_qty')) for item in moves_out])

        self.rma_qty_available = \
            float_round(quants.get(self.id, 0.0),
                        precision_rounding=self.uom_id.rounding)

        self.rma_virtual_available = \
            float_round(quants.get(self.id, 0.0) +
                        moves_in.get(self.id, 0.0) -
                        moves_out.get(self.id, 0.0),
                        precision_rounding=self.uom_id.rounding)

    rma_qty_available = fields.Float(compute='_rma_product_available',
                                     digits_compute=dp.
                                     get_precision('Product Unit '
                                                   'of Measure'),
                                     string='RMA Quantity On Hand')

    rma_virtual_available = fields.Float(compute='_rma_product_available',
                                         digits_compute=dp.
                                         get_precision('Product Unit '
                                                       'of Measure'),
                                         string='RMA Forecasted Quantity')


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    @api.one
    @api.depends('rma_qty_available', 'rma_virtual_available')
    def _rma_product_available(self):
        self.rma_qty_available = sum([p.rma_qty_available
                                      for p in
                                      self.product_variant_ids])
        self.rma_virtual_available = sum([p.rma_virtual_available
                                         for p in
                                         self.product_variant_ids])

    rma_qty_available = fields.Float(compute='_rma_product_available',
                                     digits_compute=dp.
                                     get_precision('Product Unit '
                                                   'of Measure'),
                                     string='RMA Quantity On Hand')

    rma_virtual_available = fields.Float(compute='_rma_product_available',
                                         digits_compute=dp.
                                         get_precision('Product Unit'
                                                       ' of Measure'),
                                         string='RMA Forecasted Quantity')
