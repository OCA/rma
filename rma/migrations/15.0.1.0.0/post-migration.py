# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(env.cr, "rma", "migrations/15.0.1.0.0/noupdate_changes.xml")
    openupgrade.delete_record_translations(
        env.cr,
        "rma",
        [
            "mail_template_rma_notification",
            "mail_template_rma_receipt_notification",
            "mail_template_rma_draft_notification",
        ],
    )
