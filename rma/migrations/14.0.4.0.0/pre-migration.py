# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
from odoo.tools import sql


def migrate(cr, version):
    field = "reception_move_id"
    table = "rma"
    if sql.column_exists(cr, table, field):
        cr.execute(
            "ALTER TABLE rma RENAME COLUMN reception_move_id TO reception_move_id_bak"
        )
