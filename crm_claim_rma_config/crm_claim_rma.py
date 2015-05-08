# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume
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

from openerp import models, fields


class crm_claim_type(models.Model):

    _name = 'crm.claim.type'

    name = fields.Char('Name', required=True)
    active = fields.Boolean('Active', default=True)
    description = fields.Text('Decription')


class crm_claim(models.Model):
    _inherit = 'crm.claim'

    claim_type = \
        fields.Many2one('crm.claim.type',
                        string='Claim Type',
                        help="Customer: from customer to company.\n "
                             "Supplier: from company to supplier.")
