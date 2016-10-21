# -*- coding: utf-8 -*-
#########################################################################
#                                                                       #
#                                                                       #
#########################################################################
#                                                                       #
# Copyright (C) 2009-2011  Akretion, Emmanuel Samyn                     #
#                                                                       #
# This program is free software: you can redistribute it and/or modify  #
# it under the terms of the GNU General Public License as published by  #
# the Free Software Foundation, either version 3 of the License, or     #
# (at your option) any later version.                                   #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
# GNU General Public License for more details.                          #
#                                                                       #
# You should have received a copy of the GNU General Public License     #
# along with this program.  If not, see <http://www.gnu.org/licenses/>. #
#########################################################################

{
    'name': 'Product warranty',
    'version': '8.0.1.0.0',
    'category': 'Generic Modules/Product',
    'author': "Akretion,Odoo Community Association (OCA),Vauxoo",
    'website': 'http://akretion.com',
    'license': 'AGPL-3',
    'depends': ['product'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_view.xml',
        'views/product_warranty_view.xml',
    ],
    'demo': [
        'demo/product_warranty.xml',
        'demo/res_company.xml',
    ],
    'test': [],
    'installable': True,
    'images': ['images/product_warranty.png'],
}
