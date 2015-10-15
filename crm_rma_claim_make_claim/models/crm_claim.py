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

from openerp import fields, models


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
