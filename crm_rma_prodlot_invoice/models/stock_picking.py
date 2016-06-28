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
    def action_invoice_create(self, **kwargs):
        invoices = super(StockPicking, self).action_invoice_create(**kwargs)
        self._search_serial_number_to_change_from_picking(
            invoices, kwargs.get('type'))
        return invoices

    @api.multi
    def _search_serial_number_to_change_from_picking(self,
                                                     invoices, invoice_type):
        """ A picking was generated from purchase order, because,
        the invoicing mode is that the invoice will be created
        in the picking.

        When a supplier invoice is created from a picking.
        Then, the invoice lines of invoice must be saved in
        the serial/lot number that are involved in the picking.

        The invoice line must match with the same product
        in the serial/lot number and...

        The invoice line record is saved to a maximum of
        invoice_line.quantity lots. Because, by example,
        it makes no sense that 10 serial/lot numbers have
        a invoice line with quantity = 5.

        :param invoices: The invoices of purchase order that contains
        the invoice lines to be assigned to serial/lot numbers.

        :param invoice_type: Invoice type to know what will be
        the field to change in the serial/lot number. Just for
        this module, if invoice type is 'in_invoice', then, the
        field to change will be 'supplier_invoice_line_id'

        :return: True if the process was carried out because
        a field to change in the serial/lot number was found.
        False if the invoice_type does not coincides with a
        field to change in the serial/lot number record
        """

        transfer_obj = self.env["stock.transfer_details"]
        field_to_change = \
            self._get_field_to_change_in_serial_record(invoice_type)

        if not field_to_change:
            return False

        invoice_obj = self.env['account.invoice']
        invoices_rec = invoice_obj.browse(invoices)
        invoice_lines_rec = invoices_rec.mapped("invoice_line")
        for picking in self:
            lot_ids = picking.mapped("move_lines.quant_ids.lot_id")
            transfer_obj._set_invoice_line_to_serial_numbers(
                lot_ids, invoice_lines_rec, field_to_change)
        return True

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
        field_to_change = False
        if invoice_type == "in_invoice":
            field_to_change = "supplier_invoice_line_id"
        if invoice_type == "out_invoice":
            field_to_change = "invoice_line_id"
        return field_to_change
