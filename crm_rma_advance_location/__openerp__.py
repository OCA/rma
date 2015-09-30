# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
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
    'name': 'RMA Claims Advance Location',
    'version': '8.0.1.0.0',
    'category': 'Generic Modules/CRM & SRM',
    'author': 'Akretion,Vauxoo,Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'website': 'http://www.akretion.com,http://www.vauxoo.com',
    'depends': [
        'crm_claim_rma',
    ],
    'data': [
        'wizards/claim_make_picking_from_picking_view.xml',
        'wizards/claim_make_picking_view.xml',
        'views/crm_claim.xml',
        'views/stock_picking.xml',
        'views/stock_warehouse.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False
}
