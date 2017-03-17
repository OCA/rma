# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp import fields, models


class StockMove(models.Model):

    _inherit = "stock.move"

    rma_id = fields.Many2one('rma.order.line', string='RMA',
                             ondelete='restrict')
