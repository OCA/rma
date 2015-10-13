# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP
#   Copyright (C) 2012-2014 Akretion. All Rights Reserved
#   @author Benoît GUILLOT <benoit.guillot@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################


{
    'name': 'crm_claim_categ_as_name',
    'version': '1.0',
    'category': 'Generic Modules/CRM & SRM',
    'license': 'AGPL-3',
    'description':
    """
    Replace claim name by category. It makes easier to filter on claims.
    """,
    'author': "akretion,Odoo Community Association (OCA)",
    'website': 'http://www.akretion.com/',
    'depends': ['crm_claim_rma'],
    'data': [
        'claim_view.xml',
    ],
    'demo': [],
    'installable': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
