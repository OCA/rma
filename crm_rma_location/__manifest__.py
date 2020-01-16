# Copyright 2013 Camptocampt
# Copyright 2015 Yanina Aular, Vauxoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'RMA Location',
    'version': '12.0.1.0.0',
    'author': "Camptocamp  Vauxoo, Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'website': 'https://github.com/OCA/rma',
    'category': 'Generic Modules/CRM & SRM',
    'depends': [
        'stock',
    ],
    'data': [
        'views/stock_warehouse.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False,
}
