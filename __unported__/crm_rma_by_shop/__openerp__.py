# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Joel Grand-Guillaume
#    Copyright 2013 Camptocamp SA
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

{'name': 'RMA Claims by shop',
 'version': '1.0',
 'category': 'Generic Modules/CRM & SRM',
 'depends': ['crm_claim', 'sale'
             ],
 'author': 'Camptocamp',
 'license': 'AGPL-3',
 'website': 'http://www.camptocamp.com',
 'description': """
RMA Claim by shops
==================

Claim improvements to use them by shops:

 * Add shop on claim
 * Add various filter in order to work on a basic "by shop" basis

 Was originally designed for e-commerce purpose, but could probably do the trick
 for other cases as well.

""",
 'images': [],
 'demo': [],
 'data': [
    'claim_view.xml',
 ],
 'installable': True,
 'application': True,
}
