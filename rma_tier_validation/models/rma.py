# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class RMA(models.Model):
    _name = "rma"
    _inherit = ["rma", "tier.validation"]
    _state_from = ["draft"]
    _state_to = ["confirmed"]

    _tier_validation_manual_config = False
