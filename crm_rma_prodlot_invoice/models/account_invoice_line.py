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

from openerp import _, api, models


class AccountInvoiceLine(models.Model):

    """
    Invoice Line inherited class
    """
    _inherit = 'account.invoice.line'

    @api.one
    def name_get(self):
        """
        Overwrite Odoo method like the one for
        account.invoice.line model in the
        rma module.
        """

        lot = self.move_id.lot_ids and \
            self.move_id.lot_ids[0].name or _('No lot number')

        name = _("%s - %s - Lot Number: %s") % \
                (self.invoice_id.number, self.name, lot)

        return (self.id, name)
