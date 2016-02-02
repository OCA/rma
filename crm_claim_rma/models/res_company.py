# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Coded by: Yanina Aular <yani@vauxoo.com>
#    Planified by: Yanina Aular <yani@vauxoo.com>
#    Audited by: Nhomar Hernandez <nhomar@vauxoo.com>
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

from openerp import _, api, fields, models
from openerp.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.constrains("priority_maximum", "priority_maximum")
    def _check_priority_config(self):
        for company in self:
            priority_maximum = company.priority_maximum
            priority_minimum = company.priority_minimum
            if priority_minimum <= 0 or priority_maximum <= 0:
                raise ValidationError(
                    _("Priority maximum and priority_minimum must "
                      "be greater than zero"))
            if priority_maximum >= priority_minimum:
                raise ValidationError(
                    _("Priority maximum must be less than priority_minimum"))

    @api.constrains("limit_days")
    def _check_limit_days_config(self):
        for company in self:
            if company.limit_days <= 0:
                raise ValidationError(
                    _("Limit days must be greater than zero"))

    limit_days = fields.Integer(
        help="Limit days for resolving a claim since its creation date.")
    priority_maximum = fields.Integer(
        help="Priority of a claim should be:\n"
        "- Very High: Purchase date <= priority maximum range.\n"
        "- High: priority maximum range < invoice date <= "
        "priority minimun range")
    priority_minimum = fields.Integer(
        help="Priority of a claim should be:\n"
        "- High: priority maximum range < invoice date "
        "<= priority minimun range.\n"
        "- Normal: priority minimun range < invoice date")
