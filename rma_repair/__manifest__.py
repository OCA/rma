# Copyright 2024 APSL-Nagarro Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "RMA Repair",
    "summary": "Create a repair order from rma",
    "version": "17.0.1.0.0",
    "category": "RMA",
    "website": "https://github.com/OCA/rma",
    "author": "Antoni Marroig, Odoo Community Association (OCA)",
    "maintainers": ["peluko00"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["rma_lot", "repair"],
    "data": [
        "views/rma_views.xml",
        "views/repair_views.xml",
    ],
}
