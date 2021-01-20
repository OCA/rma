# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Return Merchandise Authorization Management - Website Form",
    "summary": "Return Merchandise Authorization (RMA)",
    "version": "13.0.1.2.0",
    "development_status": "Production/Stable",
    "category": "RMA",
    "website": "https://github.com/OCA/rma",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["ernestotejeda"],
    "license": "AGPL-3",
    "depends": ["rma", "website_form"],
    "data": [
        "data/ir_model_data.xml",
        "views/assets.xml",
        "views/request_rma_form.xml",
        "views/res_config_settings_views.xml",
        "views/website_rma_portal_templates.xml",
        "views/website_templates.xml",
        "data/website_data.xml",
    ],
}
