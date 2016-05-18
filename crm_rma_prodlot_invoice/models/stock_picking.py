# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Author: Yanina Aular
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

from openerp import api, models


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    @api.multi
    def _get_field_to_change_in_serial_record(self, invoice_type):
        """ The serial/lot number can has one or two fields related
        to account.invoice.line, in this module 'out_invoice' is
        managed and 'in_invoice' (by the inherit).

        :param invoice_type: Invoice type to know what will be
        the field to change in the serial/lot number.

        If invoice type is 'in_invoice', then, the
        field to change will be 'supplier_invoice_line_id'

        If invoice type is 'out_invoice', then, the field
        to change will be 'invoice_line_id'

        :return: True if the invoice_type coincides with a field
        to change in the serial/lot number record.
        False if the invoice_type does not coincides with a
        field to change in the serial/lot number record
        """
        field_to_change = super(StockPicking, self).\
            _get_field_to_change_in_serial_record(invoice_type)
        if invoice_type == "out_invoice":
            field_to_change = "invoice_line_id"
        return field_to_change
