# -*- coding: utf-8 -*-
# © 2015 Vauxoo
# © 2014 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import api, fields, models
import openerp.addons.decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    rma_qty_available = fields.Float(
        compute='_compute_rma_template_quantities',
        digits_compute=dp.get_precision('Product Unit of Measure'),
        string='RMA Quantity On Hand'
    )
    rma_virtual_available = fields.Float(
        compute='_compute_rma_template_quantities',
        digits_compute=dp.get_precision('Product Unit of Measure'),
        string='RMA Forecasted Quantity'
    )

    @api.depends('product_variant_ids.rma_qty_available',
                 'product_variant_ids.rma_virtual_available')
    def _compute_rma_template_quantities(self):
        """ Compute rma_qty_available and rma_virtual_available
        with sum of variants quantities.
        """

        for template in self:
            qantities = template.product_variant_ids.read(
                ['rma_qty_available', 'rma_virtual_available']
            )
            template.rma_qty_available = sum(
                qty['rma_qty_available'] for qty in qantities
            )
            template.rma_virtual_available = sum(
                qty['rma_virtual_available'] for qty in qantities
            )
