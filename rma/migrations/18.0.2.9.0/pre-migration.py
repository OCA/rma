from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
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
