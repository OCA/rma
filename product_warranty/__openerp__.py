# -*- coding: utf-8 -*-
# © 2016 Yanina Aular (Vauxoo)
# © 2016 Cyril Gaudin (Camptocamp)
# © 2009-2011  Akretion, Emmanuel Samyn
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Product warranty',
    'version': '8.0.1.0.0',
    'category': 'Generic Modules/Product',
    'author': "Akretion,Odoo Community Association (OCA),Vauxoo",
    'website': 'http://akretion.com',
    'license': 'AGPL-3',
    'depends': ['product'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_view.xml',
        'views/product_warranty_view.xml',
    ],
    'demo': [
        'demo/product_warranty.xml',
        'demo/res_company.xml',
    ],
    'test': [],
    'installable': True,
    'images': ['images/product_warranty.png'],
}
