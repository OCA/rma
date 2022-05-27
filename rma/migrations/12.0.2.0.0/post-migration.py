# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Convert Text description field to Html
    openupgrade.convert_field_to_html(
        env.cr, "rma", "description", "description")
