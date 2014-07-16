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

{'name': 'RMA Claims Mass Return by Lot',
 'version': '1.0',
 'category': 'Generic Modules/CRM & SRM',
 'depends': ['crm_claim_rma'
             ],
 'author': 'Akretion',
 'license': 'AGPL-3',
 'website': 'http://www.akretion.com',
 'description': """
RMA Claim Mass Return by Lot
============================

This module adds possibility to return a whole lot of product from a Claim
and create a incoming shipment for them.


WARNING: This module is currently not yet completely debugged and is waiting his author to be.

""",
 'images': [],
 'demo': [],
 'data': [
        'wizard/returned_lines_from_serial_wizard_view.xml',
        'crm_rma_view.xml',
 ],
 'installable': False,
 'application': True,
}
