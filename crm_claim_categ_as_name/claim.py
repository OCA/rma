# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP
#   Copyright (C) 2012-2014 Akretion. All Rights Reserved
#   @author Benoît GUILLOT <benoit.guillot@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp.osv import fields, orm


class crm_claim(orm.Model):
    _inherit = 'crm.claim'

    _columns = {
        'name': fields.related(
            'categ_id',
            'name',
            relation='crm.case.categ',
            type='char',
            string='Claim Subject',
            size=128,
            store=True),
        'categ_id': fields.many2one(
            'crm.case.categ',
            'Category',
            domain="[('section_id', '=', section_id), \
                    ('object_id.model', '=', 'crm.claim')]",
            required=True),
    }
