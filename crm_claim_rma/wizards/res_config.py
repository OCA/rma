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


class RMAConfigSettings(models.TransientModel):
    _name = 'rma.config.settings'
    _inherit = 'res.config.settings'

    @api.constrains("priority_maximum", "priority_maximum")
    def _check_priority_config(self):
        for company_id in self:
            priority_max = company_id.priority_maximum
            priority_min = company_id.priority_minimum
            if priority_min <= 0 or priority_max <= 0:
                raise ValidationError(
                    _("Priority maximum and priority_minimum must "
                      "be greater than zero"))
            if priority_max >= priority_min:
                raise ValidationError(
                    _("Priority maximum must be less than priority_minimum"))

    @api.constrains("limit_days")
    def _check_limit_days_config(self):
        company_ids = self.filtered(lambda r: r.limit_days <= 0)
        if company_ids:
            raise ValidationError(_("Limit days must be greater than zero"))

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

    @api.multi
    def get_default_rma_values(self):
        """Get the current company rma configuration and
        show into the config
        wizard.
        @return dictionary with the values to display.
        """
        company_id = self.env.user.company_id
        return {
            "limit_days": company_id.limit_days,
            "priority_maximum": company_id.priority_maximum,
            "priority_minimum": company_id.priority_minimum,
        }

    @api.multi
    def set_rma_config(self):
        """Write the rma configuratin in the wizard into the company model.
        @return True
        """
        company_id = self.env.user.company_id
        for rma_config in self:
            company_id.write({
                "limit_days": rma_config.limit_days,
                "priority_maximum": rma_config.priority_maximum,
                "priority_minimum": rma_config.priority_minimum,
            })
        return True
