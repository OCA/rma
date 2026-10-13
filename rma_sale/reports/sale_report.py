# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    rma_count = fields.Integer(
        string="Number of RMAs",
        readonly=True,
    )

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res["rma_count"] = "COALESCE(l.rma_count, 0)"
        return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += """, l.rma_count"""
        return res
