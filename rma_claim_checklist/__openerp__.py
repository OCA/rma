# -*- coding: utf-8 -*-
# Copyright 2017-2018 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "RMA Claim Checklist",
    "version": "8.0.1.0.1",
    "author": "Therp BV, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Sales",
    "summary": "Create checklists to be used on Claims.",
    "depends": [
        'crm_claim',
        'crm_claim_rma',
    ],
    "data": [
        'views/rma_claim_checklist.xml',
        'views/rma_claim_checklist_question.xml',
        'views/claim_line.xml',
        'security/ir.model.access.csv',
    ],
    "installable": True,
}
