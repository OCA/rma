# -*- coding: utf-8 -*-
# © 2015 Vauxoo
# © 2017 Ursa Information Systems
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'CRM Claim RMA Code',
    'version': '10.0.1.0.0',
    'category': 'Generic Modules/CRM & SRM',
    'author': 'Vauxoo,Odoo Community Association (OCA)',
    'website': 'http://www.vauxoo.com/, http://ursainfosystems.com/',
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
