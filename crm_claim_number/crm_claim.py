# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume
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

from openerp.osv import fields, orm


# TODO add the option to split the claim_line in order to manage the same
# product separately
class crm_claim(orm.Model):
    _inherit = 'crm.claim'

    def init(self, cr):
        cr.execute("""
            UPDATE "crm_claim" SET "number"=id::varchar
            WHERE ("number" is NULL)
               OR ("number" = '/');
        """)

    def _get_sequence_number(self, cr, uid, context=None):
        seq_obj = self.pool.get('ir.sequence')
        res = seq_obj.get(cr, uid, 'crm.claim', context=context) or '/'
        return res

    def name_get(self, cr, uid, ids, context=None):
        res = []
        if isinstance(ids, (int, long)):
            ids = [ids]
        for claim in self.browse(cr, uid, ids, context=context):
            number = claim.number and str(claim.number) or ''
            res.append((claim.id, '[' + number + '] ' + claim.name))
        return res

    def create(self, cr, uid, vals, context=None):
        if ('number' not in vals) or (vals.get('number') == '/'):
            vals['number'] = self._get_sequence_number(cr, uid,
                                                       context=context)
        new_id = super(crm_claim, self).create(cr, uid, vals, context=context)
        return new_id

    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        std_default = {
            'number': self._get_sequence_number(cr, uid, context=context),
        }
        std_default.update(default)
        return super(crm_claim, self).copy_data(
            cr, uid, id, default=std_default, context=context)

    _columns = {
        'number': fields.char(
            'Number', readonly=True, required=True, select=True,
            help="Company internal claim unique number"),
    }

    _defaults = {
        'number': '/',
    }

    _sql_constraints = [
        ('number_uniq', 'unique(number, company_id)',
         'Number/Reference must be unique per Company!'),
    ]
