# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Author : Yanina Aular <yani@vauxoo.com>
#             Osval Reyes <osval@vauxoo.com>
#
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
#
##############################################################################

import datetime
from openerp import _, api, fields, models
from openerp.exceptions import Warning as UserError


class ClaimLine(models.Model):
    _inherit = 'claim.line'

    claim_line_id = fields.Many2one('claim.line',
                                    string='Related claim line',
                                    help="To link to the claim line object")

    @api.model
    def _search_related_lines(self):
        """ Search a claim line with this claim line like parent, if there is
        a line with this claim line like parent, then, the supplier claim line
        for this claim line was created """
        return self.search([('claim_line_id', '=', self.id)])

    @api.multi
    def button_create_line_rma_vendor(self):
        """ Create supplier rma product.
        """
        good_lines = []
        claim = self.env['crm.claim']
        claim_line = self.env['claim.line']
        supplier_type = self.env.ref('crm_claim_rma.crm_claim_type_supplier')
        stage_new_id = claim.with_context(
            {"default_claim_type": supplier_type.id})._get_default_stage_id()

        for claim_line_parent in self:
            claim_line_supplier = claim_line_parent._search_related_lines()

            if claim_line_supplier:
                raise UserError(
                    _('Error'),
                    _('The claim client have claim supplier created.'))

            # Search a supplier claim with new stage and add it
            # the new supplier claim line to that supplier claim
            # and to can acumulate multiples lines in a supplier
            # claim and to send to same supplier in a one travel.
            claim_supplier = claim.search([
                ('claim_type', '=', supplier_type.id),
                ('stage_id', '=', stage_new_id),
                ('partner_id', '=', claim_line_parent.supplier_id.id)])
            if not claim_supplier:
                today_datetime = datetime.datetime.now()
                today = datetime.datetime.strftime(
                    today_datetime, "%Y-%m-%d %H:%M:%S")
                deadline_datetime = today_datetime + \
                    datetime.timedelta(
                        days=self.env.user.company_id.limit_days)
                deadline = datetime.datetime.strftime(
                    deadline_datetime, "%Y-%m-%d")
                claim_supplier = claim.create({
                    'name': 'Supplier Claim',
                    'code': '/',
                    'claim_type': supplier_type.id,
                    'partner_id': claim_line_parent.supplier_id.id,
                    'categ_id': claim_line_parent.claim_id.categ_id.id,
                    'warehouse_id': claim_line_parent.claim_id.warehouse_id.id,
                    'email_from': claim_line_parent.supplier_id.email,
                    'partner_phone': claim_line_parent.supplier_id.phone,
                    'delivery_address_id': claim_line_parent.supplier_id.id,
                    'user_id': self.env.user.id,
                    'company_id': self.env.user.company_id.id,
                    'date': today,
                    'date_deadline': deadline,
                })
            elif len(claim_supplier) > 1:
                # search the supplier claim with less lines
                claims = [(claim_id, len(claim_id.claim_line_ids))
                          for claim_id in claim_supplier]
                claims = dict(claims)
                claim_supplier = min(claims, key=claims.get)

            # If the product has prodlot, the invoice_line_id
            # of supplier claim line is get from prodlot,
            # else the invoice_line_id is
            # get from supplier_invoice_id calculated in
            # claim.line
            invoice_line_for_claim_line = claim_line_parent.prodlot_id.\
                supplier_invoice_line_id
            if not invoice_line_for_claim_line:
                for line in claim_line_parent.supplier_invoice_id.invoice_line:
                    if line.product_id == claim_line_parent.product_id:
                        invoice_line_for_claim_line = line
                        break

            claim_line_supplier_new = claim_line.create({
                'name': claim_line_parent.name,
                'claim_id': claim_supplier and claim_supplier.id or False,
                'claim_type': supplier_type.id,
                'claim_line_id': claim_line_parent.id,
                'number': '/',
                'product_id': claim_line_parent.product_id.id,
                'invoice_line_id': invoice_line_for_claim_line.id,
                'claim_origin': claim_line_parent.claim_origin,
                'prodlot_id': claim_line_parent.prodlot_id.id,
                'priority': claim_line_parent.priority,
                'product_returned_quantity':
                claim_line_parent.product_returned_quantity,
            })
            good_lines += [claim_line_supplier_new.id]

        if not good_lines:
            raise UserError(_('Error'),
                            _('The Supplier Claim Was Not Created.'))

        return list(set(good_lines))

    @api.multi
    def button_rma_vendor_render_view(self):
        """
        Create supplier rma and visualize a tree view
        with new supplier claim products
        """
        good_lines = self.button_create_line_rma_vendor()
        if good_lines:
            result = self.env.ref('crm_claim_rma.act_crm_case_claim_lines')
            result = result.read()
            result[0]['domain'] = "[('id','in'," + str(good_lines) + ")]"
            return result[0]
        return True
