# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "RMA Sale Stock Picking Group By Partner By Carrier",
    "summary": "Bridge RMA sale procurement groups with grouped pickings",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "RMA",
    "website": "https://github.com/OCA/rma",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "maintainers": ["sbejaoui"],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": True,
    "depends": [
        "rma_sale",
        "stock_picking_group_by_partner_by_carrier",
    ],
}
