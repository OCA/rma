# -*- encoding: utf-8 -*-
###############################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://www.vauxoo.com>).
#    All Rights Reserved
# ############ Credits ########################################################
#    Coded by: Yanina Aular <yani@vauxoo.com>
#    Planified by: Yanina Aular <yani@vauxoo.com>
#    Audited by: Moises Lopez <moylop260@vauxoo.com>
###############################################################################
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
###############################################################################

from openerp import fields, models, api
from openerp.exceptions import except_orm
from openerp.tools.translate import _


class claim_line(models.Model):
    _inherit = 'claim.line'

    claim_line_id = fields.Many2one('claim.line',
                                    string='Related claim line',
                                    help="To link to the claim line object")


class crm_claim(models.Model):
    _inherit = 'crm.claim'

    claim_ids = \
        fields.Many2many('crm.claim',
                         'claim_rel',
                         'claim_parent',
                         'claim_child',
                         string="Related Claims",
                         help=" - For a Vendor Claim means"
                              " the RMA-C that generate the"
                              " current RMA-V.\n"
                              " - For a Custtomer Claim means"
                              " the RMA-V generated to"
                              " fullfill the current RMA-C.")

    @api.multi
    def button_create_rma_vendor(self):
        """
        Create RMA Vendor.
        """
        # TODO know serial/lot number with
        # invoice line

        # TODO warranty module with company and supplier that
        # depends of supplier module

        claim_line_obj = self.env['claim.line']
        # inv_obj = self.env['account.invoice']
        # invline_obj = self.env['account.invoice.line']
        good_lines = []

        for claim_brw in self:

            if claim_brw.claim_ids:
                raise except_orm(
                    _('Error'),
                    _('The claim client have claim supplier created.'))

            partner_claim_line_ids = {}
            # Grouping claim lines by partner (it is supplier of product)
            for cl in claim_brw.claim_line_ids:
                # If the claim line is in warranty, to do...
                if cl.supplier_id.id in partner_claim_line_ids:
                    partner_claim_line_ids.get(cl.supplier_id.id).append(cl.id)
                else:
                    partner_claim_line_ids[cl.supplier_id.id] = [cl.id]

            for partner_id in partner_claim_line_ids:
                for claim_line_id in partner_claim_line_ids.get(partner_id):

                    # Search if have claim line have a child
                    claim_lines_exists = claim_line_obj.search(
                        [('claim_line_id', '=', claim_line_id)],
                        )
                    claim_lines_exists = [cla.id for cla in claim_lines_exists]

                    # If claim_line_id does not have child
                    if not claim_lines_exists:
                        # The claim line of supplier claim is created
                        claim_line_id = claim_line_obj.browse(claim_line_id)

                        # invl = \
                        #     invline_obj.search([('invoice_id',
                        #                         '=',
                        #                          claim_line_id.
                        #                          supplier_invoice_id.id),
                        #                        ('product_id',
                        #                         '=',
                        #                         claim_line_id.product_id.id
                        #                         )])

                        claim_line_new = \
                            claim_line_id.copy({
                                'claim_id': False,
                                # 'number': '/',
                                'claim_type': 'supplier',
                                'claim_line_id': claim_line_id.id,
                                # 'state': 'draft',
                                # 'invoice_id': claim_line_id.
                                # supplier_invoice_id.id,
                                # 'supplier_invoice_id': inv_obj,
                                # 'invoice_line_id': invl[0].id,
                            })

                        # is added for display in the view
                        good_lines.append(claim_line_new.id)
                    else:
                        # Anyway. If claim line have child,
                        # is added for display in the view
                        good_lines += claim_lines_exists

            if not good_lines:
                raise except_orm(
                    _('Error'),
                    _('The Supplier Claim Was Not Created.'))
            good_lines = list(set(good_lines))
            mod_obj = self.env['ir.model.data']
            act_obj = self.env['ir.actions.act_window']

            result = mod_obj.get_object_reference('crm_claim_rma',
                                                  'act_crm_case_claim_lines')
            act_id = result and result[1] or False
            act_rec = act_obj.browse(act_id)
            result = act_rec.read()
            result[0]['domain'] = "[('id','in'," + str(good_lines) + ")]"
        return result[0]
