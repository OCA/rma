# -*- encoding: utf-8 -*-
###############################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://www.vauxoo.com>).
#    All Rights Reserved
# ############ Credits ########################################################
#    Coded by: Yanina Aular <yani@vauxoo.com>
#    Planified by: Yanina Aular <yani@vauxoo.com>
#    Audited by: Nhomar Hernandez <nhomar@vauxoo.com>
###############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from openerp import models, fields, api


class claim_line(models.Model):

    _inherit = 'claim.line'

    @api.model
    def _get_sequence_number(self):
        """
        @return the value of the secuence for the number field in the
        claim.line model.
        """
        seq_obj = self.env['ir.sequence']
        return seq_obj.get('claim.line')

    number = fields.Char(
        readonly=True,
        default='/',
        help='Claim Line Identification Number')

    # Field "number" is assigned by default with "/"
    # then this constraint ever is broken
    # _sql_constraints = [
    #     ('number_uniq', 'unique(number, company_id)',
    #         'Internal RMA number must be unique per Company!'),
    # ]

    @api.model
    def create(self, vals):
        """
        @return wirte the identify number once the claim line is create.
        """
        vals = vals or {}
        if ('number' not in vals) or (vals.get('number', False) == '/'):
            vals['number'] = self._get_sequence_number()
        res = super(claim_line, self).create(vals)
        return res

    @api.multi
    def name_get(self):
        result = []
        for cl in self:
            name = "%s - %s" % (cl.claim_id.number, cl.name)
            result.append((cl.id, name))
        return result


class crm_claim_type(models.Model):

    _inherit = 'crm.claim.type'

    ir_sequence_id = \
        fields.Many2one('ir.sequence',
                        string='Sequence Number',
                        default=lambda self:
                        self.env['ir.sequence'].
                        search([('code', '=', 'crm.claim.rma.basic')])
                        )


class crm_claim(models.Model):

    _inherit = 'crm.claim'

    rma_number = fields.Char('RMA Number', size=128,
                             help='RMA Number provided by supplier')

    def _get_sequence_number(self, cr, uid, code_id, context=None):
        seq_obj = self.pool.get('ir.sequence')
        res = '/'
        claim_type_obj = self.pool.get('crm.claim.type')
        claim_type = claim_type_obj.browse(cr, uid, code_id)
        code = claim_type.ir_sequence_id.code
        if code:
            res = seq_obj.get(cr, uid, code) or '/'
        return res

    @api.v7
    def create(self, cur, uid, vals, context=None):
        if ('number' not in vals) or (vals.get('number') == '/') \
                or vals.get('number') is False:
            vals['number'] = self._get_sequence_number(cur, uid,
                                                       vals['claim_type'],
                                                       context=context)
        new_id = super(crm_claim, self).create(cur, uid, vals, context=context)
        return new_id
