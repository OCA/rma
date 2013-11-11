# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion, 
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau, Joel Grand-Guillaume
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
    'name': 'CRM Product Return',
    'version': '1.0',
    'category': 'Generic Modules/CRM & SRM',
    'description': """
Management of Return Merchandise Authorization (RMA)
====================================================

This module aim to improve the Claims by adding a way to manage the product returns. It
allows you to create and manage picking from a claim. It also introduce a new object 
the claim lines to better handle that problematic. One Claim can have several lines that concern 
the return of differents products. It's for every of them that you'll be able to check the 
warranty (still running or not).

It mainly contain the following features :
* product returns (one by one, mass return by lot, mass return by invoice)
* warranty control & return address (based on invoice date and product form)
* product picking in / out
* product refund
* access to related customer data (orders, invoices, refunds, picking in/out)  from a claim

""",
    'author': 'Akretion, Camptocamp',
    'website': 'http://www.akretion.com',
    'depends': ['sale','stock','crm_claim','product_warranty'],
    'data': [
                'wizard/claim_make_picking_view.xml',
                'wizard/claim_make_picking_from_picking_view.xml',
                'wizard/returned_lines_from_serial_wizard_view.xml',
                'wizard/get_empty_serial_view.xml',
                'crm_claim_rma_view.xml',
                'security/ir.model.access.csv',
                'account_invoice_view.xml',
                'stock_view.xml',
                'res_company_view.xml',
                'crm_claim_rma_data.xml',
                'stock_data.xml',
    ],
    'images': ['images/product_return.png', 'images/claim.png','images/return_line.png','images/exchange.png'],
    'installable': True,
    'active': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
