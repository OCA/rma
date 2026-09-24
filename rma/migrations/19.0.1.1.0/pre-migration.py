from openupgradelib import openupgrade

from odoo.tools.sql import column_exists


@openupgrade.migrate()
def migrate(env, version):
    if not column_exists(env.cr, "rma", "parent_rma_id"):
        openupgrade.logged_query(
            env.cr,
            """
            ALTER TABLE rma
            ADD COLUMN IF NOT EXISTS parent_rma_id INTEGER
            """,
        )
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE rma
            SET parent_rma_id = move.rma_id
            FROM stock_move move
            WHERE rma.move_id = move.id
            AND move.rma_id IS NOT NULL
            """,
        )
