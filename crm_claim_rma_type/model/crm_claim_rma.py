# -*- encoding: utf-8 -*-
###############################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://www.vauxoo.com>).
#    All Rights Reserved
# ############ Credits ########################################################
#    Coded by: Yanina Aular <yani@vauxoo.com>
#    Planified by: Yanina Aular <yani@vauxoo.com>
#    Audited by: Nhomar Hernandez <nhomar@vauxoo.com>
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

from openerp import fields, api, models


class crm_claim_type(models.Model):

    _name = 'crm.claim.type'

    name = fields.Char('Name', required=True)
    active = fields.Boolean('Active')
    description = fields.Text('Decription')


class crm_claim(models.Model):

    _inherit = 'crm.claim'

    @api.model
    def _get_claim_type(self):
        claim_type = self.env['crm.claim.type']
        res = claim_type.search([('active', '=', True)])
        res = [(r.name.lower(), r.name) for r in res]
        return res

    claim_type = \
        fields.Many2one('crm.claim.type',
                        selection=_get_claim_type,
                        string='Claim Type',
                        help="Customer: from customer to company.\n "
                             "Supplier: from company to supplier.")

    stage_id = fields.Many2one('crm.claim.stage',
                               'Stage',
                               track_visibility='onchange',
                               domain="['|', ('section_ids', '=', "
                               "section_id), ('case_default', '=', True), "
                               "('claim_type', '=', claim_type)]"
                               ",('claim_default', '=', True)]")

class claim_line(models.Model):

    _inherit = 'claim.line'

    claim_type = fields.Many2one(related='claim_id.claim_type',
                                 # selection=[('customer', 'Customer'),
                                 #            ('supplier', 'Supplier')],
                                 string="Claim Line Type",
                                 store=True,
                                 help="Customer: from customer to company.\n "
                                      "Supplier: from company to supplier.")


class crm_claim_stage(models.Model):

    _inherit = 'crm.claim.stage'

    @api.model
    def _get_claim_type(self):
        return self.env['crm.claim']._get_claim_type()

    claim_type = \
        fields.Many2one('crm.claim.type',
                        selection=_get_claim_type,
                        string='Claim Type',
                        help="Customer: from customer to company.\n "
                             "Supplier: from company to supplier.")

    claim_default = fields.Boolean('Claim Type to All Teams',
                                   help="If you check this field,"
                                   " this stage will be proposed"
                                   " by default on each claim type.")
