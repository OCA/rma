# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
from odoo import SUPERUSER_ID, api
from odoo.tools import sql


def migrate(cr, version):
    field = "reception_move_id_bak"
    table = "rma"
    if sql.column_exists(cr, table, field):
        cr.execute(
            "INSERT INTO rma_stock_move_rel (rma_id, stock_move_id)"
            "SELECT id, reception_move_id_bak FROM rma WHERE reception_move_id_bak IS NOT NULL"
        )
        cr.execute("ALTER TABLE rma DROP COLUMN reception_move_id_bak")

    env = api.Environment(cr, SUPERUSER_ID, {})
    warehouses = env["stock.warehouse"].search([]).with_context(rma_post_init=True)
    for wh in warehouses:
        route_vals = wh._create_or_update_route()
        wh.write(route_vals)
