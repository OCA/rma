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
    'name': 'Product warranty',
    'version': '1.0',
    'category': 'Generic Modules/Product',
    'description': """
Product Warranty
================

Extend the product warranty management with warranty details on product / supplier relation:

* supplier warranty duration
* Set default return address for company (if different from standard one)
* return product to company, supplier, other


Those informations are used in the RMA Claim (Product Return Management) module.

""",
    'author': 'Akretion',
    'website': 'http://akretion.com',
    'depends': ['product'],
    'data': [
        'security/ir.model.access.csv',
        'res_company_view.xml',
        'product_warranty_view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
    'certificate': '',
    'images': ['images/product_warranty.png'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
