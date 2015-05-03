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


class claim_line(models.Model):

    _inherit = 'claim.line'

    @api.one
    @api.depends('guarantee_limit')
    def _set_priority(self):
        """
        To determine the priority of claim line
        """
        date_invoice = self.invoice_line_id.invoice_id.date_invoice
        if self.guarantee_limit and date_invoice:
            days = fields.datetime.strptime(self.guarantee_limit,
                                            '%Y-%m-%d') - \
                fields.datetime.strptime(date_invoice,
                                         '%Y-%m-%d')
            if days.days <= 1:
                self.priority = '3_very_high'
            elif days.days <= 7:
                self.priority = '2_high'
            else:
                self.priority = '1_normal'

    priority = fields.Selection([('0_not_define', 'Not Define'),
                                ('1_normal', 'Normal'),
                                ('2_high', 'High'),
                                ('3_very_high', 'Very High')],
                                'Priority', default='0_not_define',
                                compute='_set_priority',
                                store=True,
                                readonly=False,
                                help="Priority attention of claim line")
