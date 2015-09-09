# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Author: Osval Reyes, Yanina Aular
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api


class ClaimLine(models.Model):

    _inherit = 'claim.line'

    number = fields.Char(
        readonly=True,
        default='/',
        help='Claim Line Identification Number')

    @api.model
    def _get_sequence_number(self):
        """
        @return the value of the sequence for the number field in the
        claim.line model.
        """
        return self.env['ir.sequence'].get('claim.line')

    @api.model
    def create(self, vals):
        """
        @return write the identify number once the claim line is create.
        """
        vals = vals or {}

        if ('number' not in vals) or (vals.get('number', False) == '/'):
            vals['number'] = self._get_sequence_number()

        res = super(ClaimLine, self).create(vals)
        return res

    @api.multi
    def name_get(self):
        return [(self.id, "%s - %s" % (self.claim_id.code, self.name))]
