# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade  # pylint: disable=W7936
from psycopg2 import sql


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move_line aml
        SET rma_id = ail.rma_id
        FROM account_invoice_line ail
        WHERE ail.id = aml.old_invoice_line_id""",
    )
    openupgrade.logged_query(
        env.cr,
        sql.SQL(
            """
            UPDATE rma
            SET refund_id = am.id
            FROM account_move am
            WHERE am.old_invoice_id = {}
            """
        ).format(sql.Identifier(openupgrade.get_legacy_name("refund_id"))),
    )
    openupgrade.logged_query(
        env.cr,
        sql.SQL(
            """
            UPDATE rma
            SET refund_line_id = aml.id
            FROM account_move_line aml
            WHERE aml.old_invoice_line_id = {}
            """
        ).format(sql.Identifier(openupgrade.get_legacy_name("refund_id"))),
    )
