# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Copyright 2015 Eezee-It
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume,
#            Osval Reyes, Yanina Aular
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
    'name': 'RMA Claim (Product Return Management)',
    'version': '8.0.1.1.1',
    'category': 'Generic Modules/CRM & SRM',
    'author': "Vauxoo, "
              "Odoo Community Association (OCA)",
    'website': 'http://www.akretion.com, http://www.camptocamp.com, '
               'http://www.eezee-it.com, http://www.wearemonk.com, '
               'http://www.vauxoo.com',
    'license': 'AGPL-3',
    'depends': [
        'purchase',
        'crm_claim',
        'crm_rma_location',
        'product_warranty',
        'portal_claim',
        'default_warehouse_from_sale_team',
        'stock_unfuck',
    ],
    'data': [
        'data/ir_sequence_type.xml',
        'data/crm_claim_type.xml',
        'data/crm_claim_stage.xml',
        'data/crm_case_section.xml',
        'data/crm_case_categ.xml',
        'views/crm_claim_type.xml',
        'views/crm_claim_stage.xml',
        'views/account_invoice.xml',
        'wizards/claim_make_picking.xml',
        'views/claim_line.xml',
        'views/crm_claim.xml',
        'views/res_partner.xml',
        'views/stock_move.xml',
        'views/crm_claim_portal.xml',
        'views/res_config.xml',
        'views/res_company.xml',
        # from crm_rma_stock_location
        'wizards/claim_make_picking_from_picking_view.xml',
        'views/product_product.xml',
        'views/stock_picking.xml',
        'security/crm_claim_security.xml',
        'security/ir.model.access.csv',
        'wizards/returned_lines_from_serial_from_lot_mass.xml',
        'views/crm_claim_from_lot_mass.xml',
        'templates/assets.xml',
    ],
    'demo': [
        'demo/crm_claim_stage.xml',
        'demo/res_company.xml',
        'demo/res_partner.xml',
        'demo/account_invoice.xml',
        'demo/account_invoice_line.xml',
        'demo/res_users.xml',
        'demo/crm_claim.xml',
        'demo/claim_line.xml',
        # from crm_rma_stock_location
        'demo/stock_location.xml',
        'demo/stock_inventory.xml',
        # from lot_mass_return
        'demo/stock_production_lot_from_lot_mass.xml',
        'demo/purchase_order_from_lot_mass.xml',
        'demo/transfer_details_from_lot_mass.xml',
    ],
    'test': [
        'test/test_invoice_refund.yml'
    ],
    'installable': True,
    'auto_install': False,
    'pre_init_hook': 'create_code_equal_to_id',
    'post_init_hook': 'assign_old_sequences_and_create_locations_rma',

}
