# Copyright 2024 Raumschmiede GmbH
# Copyright 2024 BCIM
# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Rma Reason",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Raumschmiede GmbH,BCIM,ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/rma",
    "depends": ["rma"],
    "maintainers": ["sbejaoui"],
    "data": [
        "security/rma_reason.xml",
        "views/rma.xml",
        "views/rma_reason.xml",
        "views/res_config_settings.xml",
        "views/rma_portal_templates.xml",
    ],
    "demo": [
        "demo/rma_reason.xml",
    ],
}
