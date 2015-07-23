# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Original work
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    Modified work
#    Copyright (c) 2015 Eezee-It  (www.eezee-it.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.models import Model
from openerp.fields import Char, Many2one


class CrmClaim(Model):
    _inherit = 'crm.claim'

    name = Char(string='Claim Subject', size=128, store=True,
                related='categ_id.name')
    categ_id = Many2one('crm.case.categ', string='Category', required=True,
                        domain="[('section_id', '=', section_id), "
                               "('object_id.model', '=', 'crm.claim')]")
