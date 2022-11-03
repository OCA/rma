# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "RMA Tier Validation",
    "summary": "Extends the functionality of RMA Orders to "
    "support a tier validation process.",
    "version": "14.0.1.0.0",
    "category": "RMA",
    "website": "https://github.com/OCA/rma",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["rma", "base_tier_validation"],
    "data": ["views/rma_views.xml"],
}
