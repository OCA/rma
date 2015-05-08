# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'RMA Claim (Product Return Management)',
    'version': '1.2',
    'category': 'Generic Modules/CRM & SRM',
    'author': 'Akretion, Camptocamp, Vauxoo, Odoo Community Association (OCA)',
    'website': 'http://www.akretion.com, http://www.camptocamp.com',
    'depends': ['sale',
                'sales_team',
                'stock',
                'crm_claim_rma_config',
                'product_warranty',
                'crm_rma_location_rma',
                ],
    'data': ['wizard/claim_make_picking_view.xml',
             'crm_claim_rma_view.xml',
             'security/ir.model.access.csv',
             'account_invoice_view.xml',
             'stock_view.xml',
             'res_partner_view.xml',
             'crm_claim_rma_data.xml',
             ],
    'test': ['test/test_invoice_refund.yml'],
    'images': ['images/product_return.png',
               'images/claim.png',
               'images/return_line.png',
               'images/exchange.png',
               ],
    'demo': [
        'demo/crm_claim_rma_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
}
