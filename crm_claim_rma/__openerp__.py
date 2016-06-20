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
    'author': "Akretion, "
              "Camptocamp, "
              "Eezee-it, "
              "MONK Software, "
              "Vauxoo, "
              "Odoo Community Association (OCA), "
              "OdooMRP team, "
              "AvanzOSC, "
              "Serv. Tecnol. Avanzados - Pedro M. Baeza, "
              "Odoo Community Association (OCA)",
    'website': 'http://www.akretion.com, http://www.camptocamp.com, '
               'http://www.eezee-it.com, http://www.wearemonk.com, '
               'http://www.vauxoo.com',
    'license': 'AGPL-3',
    'depends': [
        'purchase',
        'sale',
        'stock',
        'crm_claim',
        'crm_claim_rma_code',
        'crm_rma_location',
        'product_warranty',
        'portal_claim',
    ],
    'data': [
        # From crm_claim_code
        'data/claim_sequence_from_code.xml',
        'views/crm_claim_from_code.xml',
        # crm_claim_type
        'data/crm_claim_type_from_type.xml',
        'data/crm_claim_stage_from_type.xml',
        'security_from_type/ir.model.access.csv',
        'views/crm_claim_from_type.xml',
        'views/crm_claim_stage_from_type.xml',
        'views/crm_claim_type_from_type.xml',
        # crm_claim_rma
        'data/ir_sequence_type.xml',
        'data/crm_case_section.xml',
        'data/crm_case_categ.xml',
        'views/account_invoice.xml',
        'wizards/claim_make_picking.xml',
        'views/crm_claim.xml',
        'views/claim_line.xml',
        'views/res_partner.xml',
        'views/stock_view.xml',
        'views/crm_claim_portal.xml',
        'security/crm_claim_security.xml',
        'views/res_config.xml',
        'views/res_company.xml',
        'views/res_users.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        # crm_claim_type
        'demo/crm_claim_from_type.xml',
        'demo/crm_claim_stage_from_type.xml',
        # crm_claim_rma
        'demo/res_company.xml',
        'demo/account_invoice.xml',
        'demo/account_invoice_line.xml',
        'demo/res_partner.xml',
        'demo/res_users.xml',
        'demo/crm_claim.xml',
        'demo/claim_line.xml',
    ],
    'test': [
        'test/test_invoice_refund.yml'
    ],
    'installable': True,
    'auto_install': False,
}
