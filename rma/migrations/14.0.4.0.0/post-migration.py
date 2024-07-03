# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    warehouses = env["stock.warehouse"].search([]).with_context(rma_post_init=True)
    for wh in warehouses:
        vals = {}
        if not wh.rma_in_type_id or not wh.rma_out_type_id:
            vals.update(wh._create_or_update_sequences_and_picking_types())
        route_vals = wh._create_or_update_route()
        vals.update(route_vals)
        wh.write(vals)
