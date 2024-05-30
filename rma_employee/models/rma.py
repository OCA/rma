# Copyright NuoBiT - Frank Cespedes <fcespedes@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class Rma(models.Model):
    _inherit = "rma"

    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        ondelete="restrict",
        domain="['|',('company_id', '=', False), ('company_id', '=', company_id)]",
    )
