# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, _


class Company(models.Model):
    _inherit = "res.company"

    @api.model
    def create(self, vals):
        company = super(Company, self).create(vals)
        company.create_rma_index()
        return company

    def create_rma_index(self):
        return self.env['ir.sequence'].sudo().create({
            'name': _('RMA Code'),
            'prefix': 'RMA',
            'code': 'rma',
            'padding': 4,
            'company_id': self.id,
        })
