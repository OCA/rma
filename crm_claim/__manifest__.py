# -*- coding: utf-8 -*-
# © 2017 Techspawn Solutions
# © 2015 Vauxoo
# © 2015 Eezee-It
# © 2009-2013 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


{
    'name': 'Claims Management yoooooo',
    'version': '1.0',
    'category': 'Sales',
    'description': """

Manage Customer Claims.
=======================
This application allows you to track your customers/vendors claims and grievances.

It is fully integrated with the email gateway so that you can create
automatically new claims based on incoming emails.
    """,
    'depends': ['crm'],
    'data': [
        'crm_claim_view.xml',
        'crm_claim_menu.xml',       
        #'security/ir.model.access.csv',
        'report/crm_claim_report_view.xml',
        'crm_claim_data.xml',
        'res_partner_view.xml',
    ],
    #'demo': ['crm_claim_demo.xml'],
    'test': [
        'test/process/claim.yml',
        'test/ui/claim_demo.yml'
    ],
    'installable': True,
    'auto_install': False,
}
