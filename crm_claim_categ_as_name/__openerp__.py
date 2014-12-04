# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
#   crm_claim_categ_as_name for OpenERP                                       #
#   Copyright (C) 2012 Akretion Benoît GUILLOT <benoit.guillot@akretion.com>  #
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as            #
#   published by the Free Software Foundation, either version 3 of the        #
#   License, or (at your option) any later version.                           #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################


{
    'name': 'crm_claim_categ_as_name',
    'version': '1.0',
    'category': 'Generic Modules/CRM & SRM',
    'license': 'AGPL-3',
    'description': """
    
    """,
    'author': 'akretion',
    'website': 'http://www.akretion.com/',
    'depends': ['crm_claim_rma'],
    'init_xml': [],
    'update_xml': [
        'crm_claim_rma_view.xml',
    ],
    'demo_xml': [], 
    'installable': False,
    'active': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
