# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    show_full_page_sale_rma = fields.Boolean(
        string="Full page RMA creation",
        help="From the frontend sale order page go to a single RMA page "
        "creation instead of the usual popup",
    )
