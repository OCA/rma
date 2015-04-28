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
        # TODO supplier module that is responsible for
        # search supplier and supplier invoice
            # TODO know serial/lot number with
            # invoice line and vice versa
            # TODO add invoice supplier field in claim line
                # TODO add supplier_id field in claim line

        # TODO warranty module with company and supplier that
        # depends of supplier module

        # TODO add claim_line_id field in claim line
        # to parent line with line
        # TODO add claim_type to claim line
        claim_line_obj = self.env['claim.line']
        invline_obj = self.env['account.invoice.line']
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

                    # If claim_line_id does not have child
                    if not claim_lines_exists:
                        # The claim line of supplier claim is created
                        claim_line_values = \
                            claim_line_obj.copy_data(claim_line_id)
                        supplier_invoice_id = \
                            claim_line_values['supplier_invoice_id']
                        claim_line_values['claim_id'] = False
                        claim_line_values['number'] = '/'
                        claim_line_values['claim_type'] = 'supplier'
                        claim_line_values['claim_line_id'] = claim_line_id
                        claim_line_values['invoice_id'] = \
                            supplier_invoice_id
                        claim_line_values['supplier_invoice_id'] = False
                        claim_line_values['state'] = 'draft'
                        invl = \
                            invline_obj.search([('invoice_id',
                                                '=',
                                                 supplier_invoice_id),
                                               ('product_id',
                                                '=',
                                                claim_line_values['product_id']
                                                )])
                        claim_line_values['invoice_line_id'] = invl[0]
                        claim_line = claim_line_obj.create(claim_line_values)

                        # is added for display in the view
                        good_lines.append(claim_line)
                    else:
                        # Anyway. If claim line have child,
                        # is added for display in the view
                        good_lines += claim_lines_exists

            if not good_lines:
                raise except_orm(
                    _('Error'),
                    _('The Supplier Claim Was Not Created.'))

            mod_obj = self.env['ir.model.data']
            act_obj = self.env['ir.actions.act_window']

            result = mod_obj.get_object_reference('crm_claim_rma',
                                                  'act_crm_case_claim_lines')
            act_id = result and result[1] or False
            result = act_obj.read([act_id])[0]
            # result['domain'] = "[('claim_line_id', '='," + \
            #    str(claim_line_id) + ")]"
            result['domain'] = "[('id','in'," + str(good_lines) + ")]"
        return result
