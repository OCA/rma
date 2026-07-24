# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Rma Repair Location",
    "summary": """Configure repair warehouse/location on RMA operations""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/rma",
    "depends": ["repair_warehouse", "rma_repair"],
    "data": ["views/rma_operation.xml"],
    "maintainers": ["sbejaoui"],
}
