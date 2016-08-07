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
from openerp import api, fields, models


class ClaimLine(models.Model):

    _inherit = 'claim.line'

    supplier_invoice_id = \
        fields.Many2one('account.invoice',
                        string='Supplier Invoice',
                        compute='_compute_supplier_and_supplier_invoice',
                        store=True,
                        help="Supplier invoice with the purchase of goods "
                        "sold to customer")
    supplier_id = \
        fields.Many2one('res.partner', string='Supplier',
                        related='supplier_invoice_id.commercial_partner_id',
                        store=True,
                        help="Supplier of good in claim")

    @api.model
    def _search_invoice_to_get_information(self, product):
        """ When the product has not serial/lot number,
        the system has not way to determine the supplier
        and supplier invoice of product.

        This method helps to search the last supplier invoice
        to get required information.
        @param product: A product.product browse to avoid
        send a id integer or a browse_list.
        This will be the product in the invoice line to be searched.
        """

        # Search one invoice with:
        # 1. max(date_invoice)
        # 2. state not in ('draft', 'cancel')
        # 3. type = 'in_invoice'
        # 4. product_id = product
        invoice_line = self.env["account.invoice.report"].search(
            [("product_id", "=", product.id),
             ("state", "not in", ("draft", "cancel")),
             ("type", "=", "in_invoice")],
            order="date desc, id desc", limit=1)

        invoice = self.env["account.invoice.line"].\
            browse(invoice_line.id).invoice_id

        return invoice

    @api.depends('prodlot_id', 'product_id')
    def _compute_supplier_and_supplier_invoice(self):
        for claim_line in self:
            if claim_line.prodlot_id:
                claim_line.supplier_id = claim_line.prodlot_id.supplier_id.id
                claim_line.supplier_invoice_id = claim_line.prodlot_id.\
                    supplier_invoice_line_id.invoice_id.id
            else:
                claim_line.supplier_invoice_id = claim_line.\
                    _search_invoice_to_get_information(claim_line.product_id)
