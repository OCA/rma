# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Convert Text description field to Html
    openupgrade.convert_field_to_html(
        env.cr, "rma", "description", "description")
    # Put the same shipping address than customer for existing RMAs
    openupgrade.logged_query(
        env.cr,
        "UPDATE rma SET partner_shipping_id = partner_id "
        "WHERE partner_shipping_id IS NULL"
    )
