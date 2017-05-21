# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Copyright 2015 Eezee-It
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume,
#            Osval Reyes, Yanina Aular
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
    'version': '8.0.1.1.1',
    'category': 'Generic Modules/CRM & SRM',
    'author': "Akretion, Camptocamp, Eezee-it, MONK Software, Vauxoo, "
              "Odoo Community Association (OCA)",
    'website': 'https://odoo-community.org',
    'license': 'AGPL-3',
    'depends': [
        'purchase',
        'sale',
        'sales_team',
        'stock',
        'crm_claim_rma_code',
        'crm_rma_location',
        'product_warranty',
    ],
    'data': [
        'data/ir_sequence_type.xml',
        'data/crm_case_section.xml',
        'data/crm_case_categ.xml',
        'views/account_invoice.xml',
        'wizards/claim_make_picking.xml',
        'views/crm_claim.xml',
        "views/claim_line.xml",
        'views/res_partner.xml',
        'views/stock_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/account_invoice.xml',
        'demo/account_invoice_line.xml',
        'demo/crm_claim.xml',
        'demo/claim_line.xml',
    ],
    'test': [
        'test/test_invoice_refund.yml'
    ],
    'installable': True,
    'auto_install': False,
}
