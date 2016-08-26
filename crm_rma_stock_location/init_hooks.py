# -*- coding: utf-8 -*-
# © 2015 Vauxoo
# © 2014-2016 Camptocamp SA
# Author: Guewen Baconnier,
#         Osval Reyes
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import SUPERUSER_ID
from openerp.api import Environment


def post_init_hook(cr, registry):
    with Environment.manage():
        env = Environment(cr, SUPERUSER_ID, {})

        warehouses = env['stock.warehouse'].search([])
        warehouses.create_locations_rma()
