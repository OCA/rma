# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Copyright 2014 Camptocamp SA
#    Author: Guewen Baconnier,
#            Osval Reyes
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
    'name': 'RMA Stock Location',
    'version': '8.0.1.0.0',
    'author': "Vauxoo,Camptocamp,Odoo Community Association (OCA)",
    'maintainer': 'Camptocamp',
    'website': 'http://www.camptocamp.com',
    'license': 'AGPL-3',
    'category': 'Generic Modules/CRM & SRM',
    'depends': [
        'crm_claim',
        'stock',
        'procurement',
        'crm_rma_location',
    ],
    'data': [
        'views/product_product.xml',
        'views/product_template.xml',
    ],
    'demo': [
        'demo/stock_location.xml',
    ],
    'installable': True,
    'auto_install': False,
}
