# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Author : Yanina Aular <yani@vauxoo.com>
#             Osval Reyes <osval@vauxoo.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
    'name': 'CRM RMA Claim Make Claim',
    'version': '8.0.1.0.0',
    'author': 'Vauxoo',
    'website': 'http://www.vauxoo.com/',
    'license': 'AGPL-3',
    'category': '',
    'depends': [
        'stock',
        'crm_claim_rma',
        'crm_claim_product_supplier',
    ],
    'data': [
        'views/crm_claim.xml',
        'views/claim_line.xml',
    ],
    'installable': True,
}
