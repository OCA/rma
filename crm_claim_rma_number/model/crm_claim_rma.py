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

from openerp import fields, api, models


class claim_line(models.Model):

    @api.model
    def _get_sequence_number(self):
        """
        @return the value of the secuence for the number field in the
        claim.line model.
        """
        seq_obj = self.env['ir.sequence']
        return seq_obj.get('claim.line')

    number = fields.Char(
        required=True, readonly=True,
        default='/',
        help='Claim Line Identification Number')

    _sql_constraints = [
        ('number_uniq', 'unique(number, company_id)',
            'Internal RMA number must be unique per Company!'),
    ]

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


class crm_claim(models.Model):

    _inherit = 'crm.claim'

    rma_number = fields.Char('RMA Number', size=128,
                             help='RMA Number provided by supplier')

    @api.model
    def _get_sequence_number_customer(self):
        seq_obj = self.env['ir.sequence']
        res = seq_obj.get('crm.claim.rma.customer') or '/'
        return res

    @api.model
    def _get_sequence_number_supplier(self):
        seq_obj = self.env['ir.sequence']
        res = seq_obj.get('crm.claim.rma.supplier') or '/'
        return res

    @api.v7
    def create(self, cur, uid, vals, context=None):
        if ('number' not in vals) or (vals.get('number') == '/'):
            if vals.get('claim_type') == 'customer':
                vals['number'] = \
                    self._get_sequence_number_customer(cur, uid,
                                                       context=context)
            elif vals.get('claim_type') == 'supplier':
                vals['number'] = \
                    self._get_sequence_number_supplier(cur, uid,
                                                       context=context)
            else:
                vals['number'] = \
                    self._get_sequence_number(cur, uid,
                                              context=context)
        new_id = super(crm_claim, self).create(cur, uid, vals, context=context)
        return new_id
