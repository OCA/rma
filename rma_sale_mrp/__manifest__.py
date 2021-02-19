# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Return Merchandise Authorization Management - Link with MRP Kits",
    "summary": "Allow doing RMAs from MRP kits",
    "version": "12.0.1.0.0",
    "development_status": "Beta",
    "category": "RMA",
    "website": "https://github.com/OCA/rma",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["chienandalu"],
    "license": "AGPL-3",
    "depends": [
        "rma_sale",
        "mrp",
    ],
    "data": [
        "views/sale_order_portal_template.xml",
        "views/rma_views.xml",
        "views/report_rma.xml",
        "wizard/sale_order_rma_wizard_views.xml",
    ],
}
