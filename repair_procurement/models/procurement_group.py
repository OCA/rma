# Copyright 2021 Jarsa
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import fields, models


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    repair_id = fields.Many2one("repair.order", "Repair Order")
