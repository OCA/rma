# -*- coding: utf-8 -*-
# © 2015 Yanina Aular, Vauxoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from . import models

from openerp import SUPERUSER_ID
from openerp.api import Environment


def post_init_hook(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})

    warehouses = env['stock.warehouse'].search([])
    warehouses.create_locations_rma()
    warehouses.create_sequences_picking_types()
