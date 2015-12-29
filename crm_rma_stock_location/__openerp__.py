# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Copyright 2013-2014 Camptocamp SA
#    Copyright 2009-2013 Akretion,
#    Author: Guewen Baconnier,
#            Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Joel Grand-Guillaume,
#            Yanina Aular, Osval Reyes
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
    'author': "Akretion,Vauxoo,Camptocamp,Odoo Community Association (OCA)",
    'maintainer': 'Camptocamp',
    'website': 'http://www.camptocamp.com,http://www.vauxoo.com',
    'license': 'AGPL-3',
    'category': 'Generic Modules/CRM & SRM',
    'depends': [
        'crm_claim_rma',
        'crm_claim',
        'stock_account',
        'procurement',
        'crm_rma_location',
    ],
    'data': [
        'wizards/claim_make_picking_from_picking_view.xml',
        'wizards/claim_make_picking_view.xml',
        'views/product_product.xml',
        'views/product_template.xml',
        'views/crm_claim.xml',
        'views/stock_picking.xml',
        'views/stock_warehouse.xml',
    ],
    'demo': [
        'demo/stock_location.xml',
        'demo/stock_inventory.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False,
}
