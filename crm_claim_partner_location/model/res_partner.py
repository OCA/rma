# -*- encoding: utf-8 -*-
###############################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://www.vauxoo.com>).
#    All Rights Reserved
# ############ Credits ########################################################
#    Coded by: Yanina Aular <yani@vauxoo.com>,
#              Katherine Zaoral <kathy@vauxoo.com>
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
from openerp.tools.translate import _


class crm_claim(models.Model):

    _inherit = 'crm.claim'

    @api.model
    def _get_related_location_options(self):
        """
        @return a list of tuples with the selection field options.
        """
        return self.env['res.partner']._get_location_options()

    @api.one
    @api.depends('partner_id', 'company_id.partner_id.country_id',
                 'company_id.country_id')
    def _get_partner_scope(self):
        self.international = self.env['res.partner']\
            ._get_partner_scope()

    international = \
        fields.Selection(related='partner_id.international',
                         readonly=True, string='Location Type',
                         selection=_get_related_location_options,
                         help='Given the partner associated to the '
                         'claim and your company'
                         ' country will tell you if the claim'
                         ' is a international or'
                         ' a local one (national). When the '
                         'company country is not'
                         ' set then will show as Undefined.')
