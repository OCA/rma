# -*- encoding: utf-8 -*-
###############################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://www.vauxoo.com>).
#    All Rights Reserved
# ############ Credits ########################################################
#    Coded by: Yanina Aular <yani@vauxoo.com>
#    Planified by: Yanina Aular <yani@vauxoo.com>
#    Audited by: Moises Lopez <moylop260@vauxoo.com>
#                Nhomar Hernandez <nhomar@vauxoo.com>
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

from openerp import models, fields, api


class crm_claim(models.Model):

    _inherit = 'crm.claim'

    @api.multi
    @api.one
    @api.depends('invoice_line_id')
    def _get_supplier_and_supplier_invoice(self):

        return False

    supplier_id = fields.Many2one('res.partner', string='Supplier',
                                  compute='_get_supplier_and_supplier_invoice',
                                  store=True,
                                  help="Supplier of good in claim")

    supplier_invoice_id = \
        fields.Many2one('account.invoice',
                        string='Supplier Invoice',
                        compute='_get_supplier_and_supplier_invoice',
                        store=True,
                        help="Supplier invoice with the "
                             "purchase of goods sold to "
                             "customer")
