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
        if kwargs.get('type') == 'in_invoice':
            self._set_invoice_line_to_serial_numbers(invoices)
        return invoices

    @api.multi
    def _set_invoice_line_to_serial_numbers(self, invoices):
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

        :return: True
        """
        prodlot_obj = self.env['stock.production.lot']
        invoice_obj = self.env['account.invoice']
        for picking in self:
            lot_ids = picking.mapped("move_lines.quant_ids.lot_id")
            for lot in lot_ids:
                # If serial/lot number has invoice line
                # ignoring the process down and continue
                # with the next serial/lot number in the
                # cycle
                if lot.supplier_invoice_line_id:
                    continue
                invoices_rec = invoice_obj.browse(invoices)
                invoice_lines_rec = invoices_rec.mapped("invoice_line")
                for inv_line in invoice_lines_rec:
                    # Search serial/lot numbers with the invoice line
                    # for take into consideration the quantity of
                    # lots with the invoice line and compared to
                    # the quantity of products in the invoice line
                    lots = prodlot_obj.search(
                        [('supplier_invoice_line_id', '=', inv_line.id)])
                    # RMA is just for product with UoM = units
                    if inv_line.product_id == lot.product_id and \
                            len(lots) < inv_line.quantity:
                        lot.write({'supplier_invoice_line_id': inv_line.id})
        return True
