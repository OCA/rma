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
        res["rma_count"] = "COUNT(DISTINCT r.id)"
        return res

    def _from_sale(self):
        res = super()._from_sale()
        res += """
            LEFT JOIN stock_move rma_sm
                ON rma_sm.sale_line_id = l.id
            LEFT JOIN rma r
                ON r.move_id = rma_sm.id
        """
        return res
