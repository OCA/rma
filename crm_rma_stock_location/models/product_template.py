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
