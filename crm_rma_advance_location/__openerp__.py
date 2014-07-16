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

{'name': 'RMA Claims Advance Location',
 'version': '1.0',
 'category': 'Generic Modules/CRM & SRM',
 'depends': ['crm_claim_rma'
             ],
 'author': 'Akretion',
 'license': 'AGPL-3',
 'website': 'http://www.akretion.com',
 'description': """
RMA Claim Advance Location
==========================

This module adds the following location on warehouses :

 * Carrier Loss
 * RMA
 * Breakage Loss 
 * Refurbish
 * Mistake Loss

And also various wizards on icoming deliveries that allow you to move your goods easily in those
new locations from a done reception.

Using this module make the logistic flow of return a bit more complexe:

 * Returning product goes into RMA location with a incoming shipment
 * From the incoming shipment, forward them to another places (stock, loss,...)

WARNING: Use with caution, this module is currently not yet completely debugged and is waiting his author to be.

""",
    'images': [],
    'demo': [],
    'data': ['wizard/claim_make_picking_from_picking_view.xml',
              'wizard/claim_make_picking_view.xml',
              'stock_view.xml',
              'stock_data.xml',
              'claim_rma_view.xml',
    ],
    'installable': True,
    'application': True,
}
