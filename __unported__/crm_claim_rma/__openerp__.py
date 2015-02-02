# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume
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
    'version': '1.1',
    'category': 'Generic Modules/CRM & SRM',
    'description': """
Management of Return Merchandise Authorization (RMA)
====================================================

This module aims to improve the Claims by adding a way to manage the
product returns. It allows you to create and manage picking from a
claim. It also introduces a new object: the claim lines to better
handle that problematic. One Claim can have several lines that
concern the return of differents products. It's for every of them
that you'll be able to check the warranty (still running or not).

It mainly contains the following features:

* product returns (one by one, mass return by invoice)
* warranty control & return address (based on invoice date and product form)
* product picking in / out
* product refund
* access to related customer data (orders, invoices, refunds, picking
  in/out) from a claim
* use the OpenERP chatter within team like in opportunity (reply to refer to
  the team, not a person)

Using this module makes the logistic flow of return this way:

* Returning product goes into Stock or Supplier location with a incoming
  shipment (depending on the settings of the supplier info in the
  product form)
* You can make a delivery from the RMA to send a new product to the Customer

.. warning:: Currently, the warranty duration used is the one configured on the
             products today, not the one which was configured when the product
             has been sold.

Contributors:
-------------

 * Emmanuel Samyn <esamyn@gmail.com>
 * Sébastien Beau <sebastien.beau@akretion.com.br>
 * Benoît Guillot <benoit.guillot@akretion.com.br>
 * Joel Grand-Guillaume <joel.grandguillaume@camptocamp.com>
 * Guewen Baconnier <guewen.baconnier@camptocamp.com>
 * Yannick Vaucher <yannick.vaucher@camptocamp.com>

""",
    'author': 'Akretion, Camptocamp',
    'website': 'http://www.akretion.com, http://www.camptocamp.com',
    'depends': ['sale',
                'stock',
                'crm_claim',
                'product_warranty',
                ],
    'data': ['wizard/claim_make_picking_view.xml',
             'crm_claim_rma_view.xml',
             'security/ir.model.access.csv',
             'account_invoice_view.xml',
             'stock_view.xml',
             'res_partner_view.xml',
             'crm_claim_rma_data.xml',
             ],
    'test': ['test/test_invoice_refund.yml'],
    'images': ['images/product_return.png',
               'images/claim.png',
               'images/return_line.png',
               'images/exchange.png',
               ],
    'installable': True,
    'auto_install': False,
}
