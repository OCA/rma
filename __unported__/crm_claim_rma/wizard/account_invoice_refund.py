# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Eezee-It
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

from openerp.models import api, TransientModel
from openerp.fields import Char

class AccountInvoiceRefund(TransientModel):
    _inherit = "account.invoice.refund"

    @api.one
    def _get_description(self):
        context = self.env.context
        if context is None:
            context = {}

        description = context.get('description') or ''
        self.description = description

    description = Char(default=_get_description)

    @api.model
    def compute_refund(self, mode='refund'):
        context = self.env.context
        if context is None:
            context = {}

        if context.get('invoice_ids'):
            context['active_ids'] = context.get('invoice_ids')

        return super(AccountInvoiceRefund, self).compute_refund(mode=mode)

