# -*- coding: utf-8 -*-
# © 2014-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models
import openerp.addons.decimal_precision as dp
from openerp.tools.safe_eval import safe_eval as eval


class ProductProduct(models.Model):

    _inherit = 'product.product'

    rma_qty_available = fields.Float(
        compute='_compute_rma_product_quantities',
        digits_compute=dp.get_precision('Product Unit of Measure'),
        search='_search_rma_product_quantity',
        string='RMA Quantity On Hand'
    )

    rma_virtual_available = fields.Float(
        compute='_compute_rma_product_quantities',
        digits_compute=dp.get_precision('Product Unit of Measure'),
        search='_search_rma_product_quantity',
        string='RMA Forecasted Quantity'
    )

    def _search_rma_product_quantity(self, operator, value):
        res = []
        # to prevent sql injections
        assert operator in ('<', '>', '=', '!=',
                            '<=', '>='), 'Invalid domain operator'
        assert isinstance(value, (float, int)), 'Invalid domain right operand'

        if operator == '=':
            operator = '=='

        ids = []
        product_ids = self.search([])
        if product_ids:
            for element in product_ids:
                localdict = {'virtual': element.rma_virtual_available,
                             'qty': element.rma_qty_available,
                             'value': value}
                if eval('qty %s value or virtual %s value' %
                        (operator, operator), localdict):
                    ids.append(element.id)
            res.append(('id', 'in', ids))
        return res

    @api.depends()
    def _compute_rma_product_quantities(self):
        """ Compute both rma_qty_available and rma_virtual_available values
        by calling product_product._product_available with RMA locations
        in context.
        """
        warehouse_model = self.env['stock.warehouse']

        locations = self.env['stock.location']

        warehouse_id = self.env.context.get('warehouse_id')
        if warehouse_id:
            warehouse = warehouse_model.browse(warehouse_id)
            if warehouse.lot_rma_id:
                locations |= warehouse.lot_rma_id

        else:
            warehouses = warehouse_model.search([('lot_rma_id', '!=', False)])
            locations |= warehouses.mapped('lot_rma_id')

        if locations:
            result = self.with_context(
                # Sorted by parent_left to avoid a little Odoo bug
                # in tests environnement
                # see https://github.com/odoo/odoo/pull/11996
                location=locations.sorted(
                    lambda l: l.parent_left
                ).mapped('id'),
            )._product_available()

        else:
            result = {}

        for product in self:
            try:
                product_qties = result[product.id]
            except KeyError:
                product.rma_qty_available = 0
                product.rma_virtual_available = 0

            else:
                product.rma_qty_available = product_qties['qty_available']
                product.rma_virtual_available = product_qties[
                    'virtual_available'
                ]
