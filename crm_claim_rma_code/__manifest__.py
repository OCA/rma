# -*- coding: utf-8 -*-
# © 2017 Techspawn Solutions
# © 2015 Vauxoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'CRM Claim RMA Code',
    'version': '9.0.1.0.0',
    'category': 'Generic Modules/CRM & SRM',
    'author': 'Vauxoo,Odoo Community Association (OCA)', 
              'Techspawn Solutions'
    'website': 'http://www.vauxoo.com/',
    'license': 'AGPL-3',
    'depends': [
        'crm_claim_type',
        'crm_claim_code',
    ],
    'data': [
        'data/ir_sequence_type.xml',
        'views/crm_claim_type.xml',
    ],
    'installable': True,
}
