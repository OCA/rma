# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Rma Batch Return",
    "summary": """This module allows to fill in the RMA batch by doing the
    return first""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/rma",
    "depends": [
        "base_partition",
        "rma_batch",
        "rma_lot",
        "web_notify",
    ],
    "data": [
        "views/rma_batch.xml",
        "views/stock_picking_type.xml",
    ],
}
