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

from openerp import _, api, exceptions, fields, models


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    claim_ids = fields.Many2many('crm.claim',
                                 'claim_rel',
                                 'claim_parent',
                                 'claim_child',
                                 string="Related Claims",
                                 help=" - For a Vendor Claim means"
                                 " the RMA-C that generates the"
                                 " current RMA-V.\n"
                                 " - For a Customer Claim means"
                                 " the RMA-V generated to"
                                      " fulfill the current RMA-C.")

    @api.multi
    def button_create_rma_vendor(self):
        """
        Create RMA Vendor.
        """

        claim_line_obj = self.env['claim.line']
        good_lines = []

        for claim_brw in self:

            if claim_brw.claim_ids:
                raise exceptions.Warning(
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

                    # Search if claim line have a child
                    claim_lines_exists = claim_line_obj.\
                        search([('claim_line_id', '=', claim_line_id)],)
                    claim_lines_exists = [cla.id for cla in claim_lines_exists]

                    # If claim_line_id does not have child
                    if not claim_lines_exists:
                        # The claim line of supplier claim is created
                        claim_line_id = claim_line_obj.browse(claim_line_id)

                        claim_line_new = \
                            claim_line_id.copy({
                                'claim_id': False,
                                'number': '/',
                                'claim_type':
                                self.env.ref('crm_claim_type.'
                                             'crm_claim_type'
                                             '_supplier').id,
                                'claim_line_id': claim_line_id.id,
                            })

                        # is added for display in the view
                        good_lines.append(claim_line_new.id)
                    else:
                        # Anyway. If claim line have child,
                        # is added for display in the view
                        good_lines += claim_lines_exists

            if not good_lines:
                raise exceptions.Warning(
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
