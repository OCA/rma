# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class RmaOperation(models.Model):
    _name = "rma.operation"
    _inherit = ["rma.operation", "restocking.fee.mixin"]
