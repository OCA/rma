# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp import fields, models


class StockWarehouse(models.Model):

    _inherit = "stock.warehouse"

    lot_rma_id = fields.Many2one('stock.location', 'RMA Location')
    rma_cust_out_type_id = fields.Many2one('stock.picking.type',
                                           'RMA Customer out Type')
    rma_sup_out_type_id = fields.Many2one('stock.picking.type',
                                          'RMA Supplier out Type')
    rma_cust_in_type_id = fields.Many2one('stock.picking.type',
                                          'RMA Customer in Type')
    rma_sup_in_type_id = fields.Many2one('stock.picking.type',
                                         'RMA Supplier in Type')
