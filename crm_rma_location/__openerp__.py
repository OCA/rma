# -*- coding: utf-8 -*-
# © Guewen Yanina Aular, Vauxoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'RMA Location',
    'version': '9.0.1.0.0',
    'author': "Vauxoo, Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'website': 'http://www.camptocamp.com,http://www.vauxoo.com',
    'category': 'Generic Modules/CRM & SRM',
    'depends': [
        'stock',
        'procurement',
    ],
    'data': [
        'views/stock_warehouse.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False,
}
