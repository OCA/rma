# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Rma Sale Stock Restocking Fee Invoicing",
    "summary": """Extends the RMA flow to automatically apply fixed or percentage
    restocking fees.""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "maintainers": ["sbejaoui"],
    "website": "https://github.com/OCA/rma",
    "depends": [
        "sale_stock_restocking_fee_invoicing",
        "rma_sale",
        "stock_move_propagate_first_move",
    ],
    "data": ["views/rma_operation.xml", "views/rma.xml"],
    "demo": [],
}
