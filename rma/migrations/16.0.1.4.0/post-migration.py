# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Similar behavior to create_rma_routes of post_init_hook."""
    warehouses = env["stock.warehouse"].search([])
    warehouses = warehouses.with_context(rma_post_init_hook=True)
    for wh in warehouses:
        route_vals = wh._create_or_update_route()
        wh.write(route_vals)
