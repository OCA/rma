# -*- coding: utf-8 -*-
#########################################################################
#                                                                       #
#                                                                       #
#########################################################################
#                                                                       #
# Copyright (C) 2009-2011  Akretion, Emmanuel Samyn                     #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################


{
    'name': 'CRM claim extension',
    'version': '1.0',
    'category': 'Generic Modules/CRM & SRM',
    'description': """
Akretion - Emmanuel Samyn
Add some fields to CRM claim : canal, spirit
    """,
    'author': 'Akretion',
    'website': 'http://www.akretion.com',
    'depends': ['crm_claim'],
    'init_xml': [],
    'update_xml': [
        'crm_claim_ext_view.xml',
    ],
    'demo_xml': [], 
    'test': [], 
    'installable': True,
    'active': False,
    'certificate' : '',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
