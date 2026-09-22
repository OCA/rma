# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Rma Sale Auto Detect",
    "summary": """Automatically link RMA products to related sales orders within an
    eligibility period""",
    "version": "18.0.1.0.2",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/rma",
    "depends": ["rma_sale"],
    "data": ["views/rma.xml", "views/rma_operation.xml"],
    "demo": [],
}
