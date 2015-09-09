# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume,
#            Osval Reyes, Yanina Aular
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
from openerp import _, api, models


class AccountInvoiceLine(models.Model):
    """
    Account Invoice Line
    """

    _inherit = "account.invoice.line"

    @api.model
    def create(self, vals):
        claim_line_id = vals.get('claim_line_id')
        if claim_line_id:
            del vals['claim_line_id']

        line = super(AccountInvoiceLine, self).create(vals)
        if claim_line_id:
            claim_line = self.env['claim.line'].browse(claim_line_id)
            claim_line.refund_line_id = line.id

        return line

    def name_get(self, cr, user, ids, context=None):
        """
        overwrite openerp method like the one for
        account.invoice.line model in the
        rma module.
        """
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        result = []
        if not len(ids):
            return result
        for ail in self.browse(cr, user, ids, context=context):
            lot = ail.move_id.lot_ids and \
                ail.move_id.lot_ids[0].name or _('No lot number')
            name = _("%s - %s - Lot Number: %s") % \
                (ail.invoice_id.number, ail.name, lot)
            result.append((ail.id, name))
        return result
