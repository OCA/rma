# -*- coding: utf-8 -*-
# © 2015 Vauxoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class CrmClaimType(models.Model):

    _inherit = 'crm.claim.type'

    ir_sequence_id = \
        fields.Many2one('ir.sequence',
                        string='Sequence Code',
                        default=lambda self: self.env['ir.sequence'].
                        search([('code', '=', 'crm.claim.rma.basic')])
                        )
