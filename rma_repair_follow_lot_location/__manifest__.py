# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Rma Repair Follow Lot Location",
    "summary": """This addon define default value for repair order follow_lot_location
    field from rma reason""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/rma",
    "maintainers": ["sbejaoui"],
    "depends": ["repair_follow_lot_location", "rma_repair"],
    "data": ["views/rma_operation.xml"],
}
