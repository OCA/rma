# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade

from odoo.tools.sql import column_exists


def migrate(cr, version):
    # sale_line_id column to rma table
    if not column_exists(cr, "rma", "sale_line_id"):
        openupgrade.logged_query(
            cr,
            """
            ALTER TABLE rma
            ADD COLUMN IF NOT EXISTS sale_line_id INTEGER
            """,
        )
        openupgrade.logged_query(
            cr,
            """
            UPDATE rma AS r
            SET sale_line_id = sm.sale_line_id
            FROM stock_move AS sm
            WHERE sm.id = r.move_id
            AND r.sale_line_id IS DISTINCT FROM sm.sale_line_id
            """,
        )
    # rma_count column to sale_order_line table
    if not column_exists(cr, "sale_order_line", "rma_count"):
        openupgrade.logged_query(
            cr,
            """
            ALTER TABLE sale_order_line
            ADD COLUMN IF NOT EXISTS rma_count INTEGER
            """,
        )
        openupgrade.logged_query(
            cr,
            """
            UPDATE sale_order_line
            SET rma_count = 0
            WHERE rma_count IS NULL
            """,
        )
        openupgrade.logged_query(
            cr,
            """
            UPDATE sale_order_line AS sol
            SET rma_count = counts.rma_count
            FROM (
                SELECT sale_line_id, COUNT(*) AS rma_count
                FROM rma
                WHERE sale_line_id IS NOT NULL
                GROUP BY sale_line_id
            ) AS counts
            WHERE sol.id = counts.sale_line_id
            """,
        )
