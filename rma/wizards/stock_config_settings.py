# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp import models, fields


class StockConfigSettings(models.Model):
    _inherit = 'stock.config.settings'

    group_rma_delivery_address = fields.Selection([
        (0, "Invoicing and shipping addresses are always the same "
            "(Example: services companies)"),
        (1, 'Display 3 fields on rma: partner, invoice address, delivery '
            'address')
        ], "Addresses",
        implied_group='rma.group_rma_delivery_invoice_address')
