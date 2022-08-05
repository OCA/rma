# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Return Merchandise Authorization Management - Link with Sales",
    "summary": "Sale Order - Return Merchandise Authorization (RMA)",
    "version": "13.0.1.1.0",
    "development_status": "Production/Stable",
    "category": "RMA",
    "website": "https://github.com/OCA/rma",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["ernestotejeda"],
    "license": "AGPL-3",
    "depends": ["rma", "sale_stock"],
    "data": [
        "views/assets.xml",
        "views/report_rma.xml",
        "views/rma_views.xml",
        "views/sale_views.xml",
        "views/sale_portal_template.xml",
        "wizard/sale_order_rma_wizard_views.xml",
    ],
}
