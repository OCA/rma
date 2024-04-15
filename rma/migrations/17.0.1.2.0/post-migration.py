# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Similar behavior to create_rma_routes of post_init_hook."""
    warehouses = env["stock.warehouse"].search([])
    warehouses = warehouses.with_context(rma_post_init_hook=True)
    for wh in warehouses:
        if not wh.rma_in_type_id or not wh.rma_out_type_id:
            data = wh._create_or_update_sequences_and_picking_types()
            wh.write(data)
        route_vals = wh._create_or_update_route()
        wh.write(route_vals)
