from openupgradelib import openupgrade

_renamed_fields = [
    ("rma", "rma", "procurement_group_id", "stock_reference_id"),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, _renamed_fields)
