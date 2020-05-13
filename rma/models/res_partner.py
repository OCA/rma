# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    rma_ids = fields.One2many(
        comodel_name='rma',
        inverse_name='partner_id',
        string='RMAs',
    )
    rma_count = fields.Integer(
        string='RMA count',
        compute='_compute_rma_count',
    )

    def _compute_rma_count(self):
        rma_data = self.env['rma'].read_group(
            [('partner_id', 'in', self.ids)], ['partner_id'], ['partner_id'])
        mapped_data = dict(
            [(r['partner_id'][0], r['partner_id_count']) for r in rma_data])
        for record in self:
            record.rma_count = mapped_data.get(record.id, 0)

    def action_view_rma(self):
        self.ensure_one()
        action = self.env.ref('rma.rma_action').read()[0]
        rma = self.rma_ids
        if len(rma) == 1:
            action.update(
                res_id=rma.id,
                view_mode="form",
                view_id=False,
                views=False,
            )
        else:
            action['domain'] = [('partner_id', 'in', self.ids)]
        return action
