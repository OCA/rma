# -*- coding: utf-8 -*-
# Copyright 2016 ADHOC SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openupgradelib import openupgrade

xmlid_renames = [
    (
        'crm_claim_rma.section_after_sales_service',
        'crm_claim_rma.team_after_sales_service',
    )
]


@openupgrade.migrate()
def migrate(cr, version):
    openupgrade.rename_xmlids(cr, xmlid_renames)
