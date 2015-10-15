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

from openerp import _, api, fields, models
from openerp.exceptions import Warning as UserError


class ClaimLine(models.Model):
    _inherit = 'claim.line'

    claim_line_id = fields.Many2one('claim.line',
                                    string='Related claim line',
                                    help="To link to the claim line object")

    @api.multi
    def button_create_line_rma_vendor(self):
        """
        Create RMA Vendor.
        """
        good_lines = []
        claim_obj = self.env['crm.claim']
        claim_line_obj = self.env['claim.line']
        claim_type_supplier = self.env.\
            ref('crm_claim_type.crm_claim_type_supplier')
        stage_new = self.env.ref('crm_claim.stage_claim1')

        for claim_line_parent in self:
            # Search a claim line with this claim line
            # like parent, if there is a line with
            # this claim line like parent, then, the
            # supplier claim line for this claim line
            # was created
            claim_line_supplier = \
                claim_line_obj.search([('claim_line_id',
                                        '=',
                                        claim_line_parent.id)])
            if claim_line_supplier:
                raise UserError(
                    _('Error'),
                    _('The claim client have claim supplier created.'))

            # Search a supplier claim with new stage and add it
            # the new supplier claim line to that supplier claim
            # and to can acumulate multiples lines in a supplier
            # claim and to send to same supplier in a one travel.
            claim_supplier = claim_obj.search([('claim_type', '=',
                                                claim_type_supplier.id),
                                               ('stage_id', '=', stage_new.id),
                                               ('partner_id', '=',
                                                claim_line_parent.
                                                supplier_id.id)])
            if not claim_supplier:
                claim_supplier = claim_obj.create({
                    'name': 'Supplier Claim',
                    'code': '/',
                    'claim_type': claim_type_supplier.id,
                    'partner_id': claim_line_parent.supplier_id.id,
                    'categ_id': claim_line_parent.claim_id.categ_id.id,
                    'warehouse_id': claim_line_parent.claim_id.warehouse_id.id,
                    'email_from': claim_line_parent.supplier_id.email,
                    'partner_phone': claim_line_parent.supplier_id.phone,
                    'delivery_address_id': claim_line_parent.supplier_id.id,
                })
            elif len(claim_supplier) > 1:
                # search the supplier claim with less lines
                claims = [(claim, len(claim.claim_line_ids))
                          for claim in claim_supplier]
                claims = dict(claims)
                claim_supplier = min(claims, key=claims.get)
            claim_line_supplier_new = \
                claim_line_obj.create({
                    'name': claim_line_parent.name,
                    'claim_id': claim_supplier and claim_supplier.id or False,
                    'claim_type': claim_type_supplier.id,
                    'claim_line_id': claim_line_parent.id,
                    'number': '/',
                    'product_id': claim_line_parent.product_id.id,
                    'invoice_line_id': claim_line_parent.prodlot_id.
                    supplier_invoice_line_id.id,
                    'claim_origin': claim_line_parent.claim_origin,
                    'prodlot_id': claim_line_parent.prodlot_id.id,
                    'priority': claim_line_parent.priority,
                })
            good_lines += [claim_line_supplier_new.id]

            if not good_lines:
                raise UserError(
                    _('Error'),
                    _('The Supplier Claim Was Not Created.'))

            good_lines = list(set(good_lines))

            result = self.env.ref('crm_claim_rma.'
                                  'act_crm_case_claim_lines')
            result = result.read()

        result[0]['domain'] = "[('id','in'," + str(good_lines) + ")]"
        return result

    @api.multi
    def button_rma_vendor_render_view(self):
        result = self.button_create_line_rma_vendor()
        return result[0]
