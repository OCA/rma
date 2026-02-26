# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RmaOperation(models.Model):

    _inherit = "rma.operation"

    repair_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Repair Warehouse",
        help="If set, repair orders created from this operation will use this warehouse.",
    )
    repair_location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Repair Location",
        domain="[('warehouse_id', '=', repair_warehouse_id)]",
        help="If set, repair orders created from this operation will use this location.",
    )
