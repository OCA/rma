# -*- coding: utf-8 -*-
# © 2015 Vauxoo
# © 2015 Eezee-It
# © 2009-2013 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'RMA Claim (Product Return Management)',
    'version': '9.0.1.0.0',
    'category': 'Generic Modules/CRM & SRM',
    'author': "Akretion, Camptocamp, Eezee-it, MONK Software, Vauxoo, "
              "Odoo Community Association (OCA)",
    'website': 'http://www.akretion.com, http://www.camptocamp.com, '
               'http://www.eezee-it.com, http://www.wearemonk.com, '
               'http://www.vauxoo.com',
    'license': 'AGPL-3',
    'depends': [
        'purchase',
        'sale',
        'crm',
        'stock',
        'crm_rma_location',
        'product_warranty',
    ],
    'data': [
        'data/claim_sequence.xml',
        'data/crm_claim_type.xml',
        'data/crm_claim_stage.xml',
        'data/ir_sequence_type.xml',
        'data/crm_team.xml',
        'data/crm_claim_category.xml',
        'wizards/claim_make_picking.xml',
        'views/crm_claim.xml',
        'views/crm_claim_view.xml',
        'views/crm_claim_type.xml',
        'views/crm_claim_menu.xml',
        'views/account_invoice.xml',
        "views/claim_line.xml",
        'views/res_partner.xml',
        'views/stock_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'data/crm_claim_demo.xml',
    ],
    'test': [
        'test/test_invoice_refund.yml'
    ],
    'installable': False,
    'auto_install': False,
}
