# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Copyright 2015 Eezee-It
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Joel Grand-Guillaume
#            Osval Reyes, Yanina Aular
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

from openerp import SUPERUSER_ID
from . import models
from . import wizards
from . import exceptions


def create_code_equal_to_id(cr):
    cr.execute('ALTER TABLE crm_claim ADD COLUMN code character varying;')
    cr.execute('UPDATE crm_claim SET code = id;')


def assign_old_sequences_and_create_locations_rma(cr, registry):
    # Assign old sequence
    claim_obj = registry['crm.claim']
    sequence_obj = registry['ir.sequence']
    claim_ids = claim_obj.search(cr, SUPERUSER_ID, [], order="id")
    for claim_id in claim_ids:
        cr.execute('UPDATE crm_claim SET code = %s WHERE id = %s;',
                   (sequence_obj.get(cr, SUPERUSER_ID, 'crm.claim.rma.basic'),
                    claim_id))

    # Create locations rma
    stock_wh = registry['stock.warehouse']
    for wh_id in stock_wh.browse(cr, SUPERUSER_ID,
                                 stock_wh.search(cr, SUPERUSER_ID, [])):
        vals = stock_wh.create_locations_rma(cr, SUPERUSER_ID, wh_id)
        stock_wh.write(cr, SUPERUSER_ID, wh_id.id, vals)
