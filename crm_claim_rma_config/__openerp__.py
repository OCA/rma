# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yanina Aular
#    Copyright 2015 Vauxoo
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
    'name': 'RMA Claim Config',
    'version': '1.0',
    'category': 'Generic Modules/CRM & SRM',
    'author': 'Vauxoo, Odoo Community Association (OCA)',
    'website': 'http://www.vauxoo.com',
    'depends': ['base',
                'crm_claim',
                ],
    'data': [
            'crm_claim_rma_data.xml',
            'view/crm_claim_rma_view.xml',
            'security/ir.model.access.csv',
    ],
    'test': [],
    'images': [],
    'demo': ['crm_claim_rma_demo.xml'],
    'installable': True,
    'auto_install': False,
}
