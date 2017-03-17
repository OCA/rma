# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

{
    'name': 'Return Merchandise Authorization (RMA)',
    'version': '9.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'RMA',
    'summary': 'Introduces the return merchandise authorization (RMA) process '
               'in odoo',
    "author": "Eficent, "
              "Odoo Community Association (OCA)",
    'website': 'http://www.github.com/OCA/rma',
    'depends': ['account', 'stock', 'mail'],
    'data': ['security/rma.xml',
             'security/ir.model.access.csv',
             'views/rma_view.xml',
             'views/stock_view.xml',
             'views/stock_warehouse.xml',
             'views/invoice_view.xml',
             'views/product_view.xml',
             'wizards/rma_make_picking.xml',
             'wizards/rma_refund.xml',
             'wizards/stock_config_settings.xml',
             'data/stock.xml'],
    'installable': True,
    'auto_install': False,
}
