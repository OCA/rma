# -*- coding: utf-8 -*-
#########################################################################
#                                                                       #
#                                                                       #
#########################################################################
#                                                                       #
# Copyright (C) 2009-2011  Akretion, Raphaël Valyi, Sébastien Beau,     #
# Emmanuel Samyn, Benoît Guillot                                        #
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
    'name': 'CRM Product Return',
    'version': '1.0',
    'category': 'Generic Modules/CRM & SRM',
    'description': """
Akretion - Emmanuel Samyn
Management of Return Merchandise Authorization (RMA) in OpenERP.
Upgrade the standard crm_claim module to add :
* product returns (one by one, mass return by lot, mass return by invoice)
* warranty control & return address (based on invoice date and product form)
* product picking in / out
* product refund
* product exchange
* access to related customer data (orders, invoices, refunds, picking in/out)

THIS MODULE REPLACES Akretion stock_rma from V6.0
    
WARNING : To use the module in V6.1 you need a refactor of the function refund
in the module account from the addons. You can find the refactor at the revisions 6933 and 6934
on this branch : https://code.launchpad.net/~akretion-team/openobject-addons/openobject-addons-61-akretion
    
    """,
    'author': 'esamyn',
    'website': 'http://www.erp-236.com',
    'depends': ['sale','stock','crm_claim','product_warranty'],
    'init_xml': ['rma_data.xml',],
    'update_xml': [
                'wizard/claim_make_picking_view.xml',
                'wizard/claim_make_picking_from_picking_view.xml',
                'wizard/returned_lines_from_serial_wizard_view.xml',
#                'wizard/returned_lines_from_invoice_wizard_view.xml',
#                'wizard/picking_from_returned_lines_wizard_view.xml',
#                'wizard/refund_from_returned_lines_wizard_view.xml',
#                'wizard/exchange_from_returned_lines_wizard_view.xml',
#                'wizard/picking_from_exchange_lines_wizard_view.xml',
                'wizard/get_empty_serial_view.xml',
                'crm_claim_rma_view.xml',
                'security/ir.model.access.csv',
                'account_invoice_view.xml',
                'stock_view.xml',
                'res_company_view.xml',
                'crm_claim_rma_data.xml',
                'stock_data.xml',
 #       'report/crm_claim_report_view.xml',
    ],
    'demo_xml': [
 #       'crm_claim_demo.xml',
    ], 
#    'test': ['test/test_crm_claim.yml'], 
    'images': ['images/product_return.png', 'images/claim.png','images/return_line.png','images/exchange.png'],
    'installable': True,
    'active': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
