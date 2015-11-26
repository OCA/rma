# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Copyright 2014 Camptocamp SA
#    Author: Guewen Baconnier,
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

from openerp import _, models, fields
import openerp.addons.decimal_precision as dp


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    rma_qty_available = fields.Float(compute='_rma_product_available',
                                     digits_compute=dp.
                                     get_precision('Product Unit '
                                                   'of Measure'),
                                     string=_('RMA Quantity On Hand'))

    rma_virtual_available = fields.Float(compute='_rma_product_available',
                                         digits_compute=dp.
                                         get_precision('Product Unit'
                                                       ' of Measure'),
                                         string=_('RMA Forecasted Quantity'))

    def _rma_product_available(self):
        for product in self:
            product.rma_qty_available = sum(
                [p.rma_qty_available for p in product.product_variant_ids])
            product.rma_virtual_available = sum(
                [p.rma_virtual_available for p in product.product_variant_ids])
