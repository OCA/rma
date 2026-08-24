# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "RMA Batch Reason",
    "summary": """Add reason field to RMA batches and propagate to RMAs""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/rma",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "depends": [
        "rma_batch",
        "rma_reason",
    ],
    "data": [
        "views/rma_batch.xml",
    ],
    "installable": True,
}
