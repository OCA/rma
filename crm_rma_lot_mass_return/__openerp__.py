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
    'name': 'RMA Claims Mass Return by Lot',
    'version': '8.0.1.0.0',
    'category': 'Generic Modules/CRM & SRM',
    'author': 'Vauxoo,Akretion,Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'website': 'https://odoo-community.org',
    'depends': [
        'crm_claim_rma',
        'crm_rma_prodlot_invoice',
        'crm_rma_prodlot_supplier',
    ],
    'data': [
        'wizards/returned_lines_from_serial_wizard.xml',
        'views/crm_claim.xml',
        'templates/search_view.xml'
    ],
    'demo': [
        'demo/stock_production_lot.xml',
        'demo/purchase_order.xml',
        'demo/sale_order.xml',
        'demo/transfer_details.xml',
    ],
    'installable': True,
    'auto_install': False
}
