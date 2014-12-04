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
from openerp.osv import orm


class account_invoice_refund(orm.TransientModel):

    _inherit = "account.invoice.refund"

    def compute_refund(self, cr, uid, ids, mode='refund', context=None):
        if context is None:
            context = {}
        if context.get('invoice_ids'):
            context['active_ids'] = context.get('invoice_ids')
        return super(account_invoice_refund, self).compute_refund(
            cr, uid, ids, mode=mode, context=context)

    def _get_description(self, cr, uid, context=None):
        if context is None:
            context = {}
        description = context.get('description') or ''
        return description

    _defaults = {
        'description': _get_description,
    }
