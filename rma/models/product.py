# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    rma_operation = fields.Selection([('refund', 'Refund'),
                                      ('repair', 'Receive and repair'),
                                      ('replace', 'Replace')],
                                     string="Default RMA Operation",
                                     default='replace')
