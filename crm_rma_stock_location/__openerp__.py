# -*- coding: utf-8 -*-
# Author: Guewen Baconnier,
#         Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#         Joel Grand-Guillaume,
#         Yanina Aular, Osval Reyes
#
# © 2009-2013 Akretion
# © 2014-2016 Camptocamp SA
# © 2015 Vauxoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


{
    'name': 'RMA Stock Location',
    'version': '9.0.1.0.0',
    'author': "Akretion,Vauxoo,Camptocamp,Odoo Community Association (OCA)",
    'maintainer': 'Camptocamp',
    'website': 'http://www.camptocamp.com,http://www.vauxoo.com',
    'license': 'AGPL-3',
    'category': 'Generic Modules/CRM & SRM',
    'depends': [
        'crm_claim_rma',
        'crm_claim',
        'stock_account',
        'procurement',
        'crm_rma_location',
    ],
    'data': [
        'wizards/claim_make_picking_from_picking_view.xml',
        'wizards/claim_make_picking_view.xml',
        'views/product_product.xml',
        'views/product_template.xml',
        'views/crm_claim.xml',
        'views/stock_picking.xml',
        'views/stock_warehouse.xml',
    ],
    'demo': [
        'demo/stock_location.xml',
        'demo/stock_inventory.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False,
}
