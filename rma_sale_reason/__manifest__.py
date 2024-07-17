# Copyright 2024 Raumschmiede GmbH
# Copyright 2024 BCIM
# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Rma Sale Reason",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Raumschmiede GmbH,BCIM,ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/rma",
    "depends": ["rma_sale", "rma_reason"],
    "maintainers": ["sbejaoui"],
    "data": [
        "wizards/sale_order_rma_wizard.xml",
        "views/rma_portal_templates.xml",
    ],
    "demo": [],
    "assets": {
        "web.assets_frontend": [
            "/rma_sale_reason/static/src/js/rma_portal_form.js",
        ],
        "web.assets_tests": [
            "/rma_sale_reason/static/src/tests/*.js",
        ],
    },
}
