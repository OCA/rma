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

from openerp import models, api


class crm_claim(models.Model):

    _inherit = 'crm.claim'

    @api.model
    def _get_stock_moves_with_code(self, code='incoming'):
        """
        @code: Type of operation code.
        Returns all stock_move with filtered by type of
        operation.
        """
        stockmove = self.env['stock.move']
        receipts = self.env['stock.picking.type']

        spt_receipts = receipts.search([('code',
                                         '=',
                                         code)])
        spt_receipts = [spt.id for spt in spt_receipts]

        sm_receipts = stockmove.search([('picking_type_id',
                                         'in',
                                         spt_receipts)])
        return sm_receipts

