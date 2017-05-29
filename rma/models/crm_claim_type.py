# -*- coding: utf-8 -*-
# © 2015 Vauxoo: Yanina Aular <yani@vauxoo.com>, Osval Reyes <osval@vauxoo.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CrmClaimType(models.Model):
    """
        CRM Claim Type
    """
    _name = 'crm.claim.type'

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
    description = fields.Text(translate=True)
    ir_sequence_id = \
        fields.Many2one('ir.sequence',
                        string='Sequence Code',
                        default=lambda self: self.env['ir.sequence'].
                        search([('code', '=', 'crm.claim.rma.basic')])
                        )
