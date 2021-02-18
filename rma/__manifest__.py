# Copyright 2020 Tecnativa - Ernesto Tejeda
# Copyright 2020 Tecnativa - David Vidal
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Return Merchandise Authorization Management",
    "summary": "Return Merchandise Authorization (RMA)",
    "version": "12.0.2.1.0",
    "development_status": "Production/Stable",
    "category": "RMA",
    "website": "https://github.com/OCA/rma",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["ernestotejeda"],
    "license": "AGPL-3",
    "depends": [
        "account",
        "stock",
    ],
    "data": [
        "views/report_rma.xml",
        "report/report.xml",
        "data/mail_data.xml",
        "data/rma_operation_data.xml",
        "data/stock_data.xml",
        "security/rma_security.xml",
        "security/ir.model.access.csv",
        "wizard/stock_picking_return_views.xml",
        "wizard/rma_delivery_views.xml",
        "wizard/rma_split_views.xml",
        "views/menus.xml",
        "views/res_partner_views.xml",
        "views/rma_portal_templates.xml",
        "views/rma_team_views.xml",
        "views/rma_views.xml",
        "views/stock_picking_views.xml",
        "views/stock_warehouse_views.xml",
        "views/res_config_settings_views.xml",
    ],
    'post_init_hook': 'post_init_hook',
    "application": True,
}
