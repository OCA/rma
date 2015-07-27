# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume
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
    'name': 'Claim number',
    'version': '1.0',
    'category': 'Generic Modules/CRM & SRM',
    'author': "Akretion, Camptocamp,Odoo Community Association (OCA)",
    'website': 'http://www.akretion.com, http://www.camptocamp.com',
    'license': 'AGPL-3',
    'depends': ['crm_claim'],
    'data': ['crm_claim_view.xml',
             'crm_claim_data.xml',
             ],
    'installable': True,
    'auto_install': False,
}
