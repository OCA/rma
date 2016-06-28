# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Author: Yanina Aular, Osval Reyes
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
    'name': 'CRM Claim Prodlot Invoice',
    'version': '8.0.1.0.0',
    'author': 'Vauxoo,Odoo Community Association (OCA)',
    'website': 'http://www.vauxoo.com/',
    'category': 'RMA',
    'license': 'AGPL-3',
    'depends': [
        'purchase',
        'sale_stock',
        'product_unique_serial',
        'crm_claim',
    ],
    'data': [
        'views/stock_transfer_details.xml',
        'views/stock_production_lot.xml',
    ],
    'installable': True,
}
