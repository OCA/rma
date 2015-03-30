# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2014 Camptocamp SA
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

{'name': 'RMA Stock Location',
 'version': '1.0',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'maintainer': 'Camptocamp',
 'license': 'AGPL-3',
 'category': 'Generic Modules/CRM & SRM',
 'depends': ['stock',
             'procurement',
             'crm_rma_location_rma',
             ],
 'description': """
RMA Stock Location
==================

A RMA location can be selected on the warehouses.
The product views displays the quantity available and virtual in this
 RMA location (including the children locations).

 """,
 'website': 'http://www.camptocamp.com',
 'data': ['stock_data.xml',
          'product_view.xml',
          ],
 'demo': ['stock_demo.xml',
          ],
 'test': ['test/quantity.yml',
          ],
 'installable': True,
 'auto_install': False,
 }
