# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Return Merchandise Authorization Management - Link with deliveries",
    "summary": "Allow to choose a default delivery carrier for returns",
    "version": "18.0.1.4.0",
    "development_status": "Beta",
    "category": "RMA",
    "website": "https://github.com/OCA/rma",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["chienandalu"],
    "license": "AGPL-3",
    "depends": ["rma", "stock_delivery"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/rma_views.xml",
        "wizard/rma_choose_delivery_carrier_views.xml",
        "wizard/rma_rma_wizard_views.xml",
        "wizard/stock_picking_return_views.xml",
    ],
}
