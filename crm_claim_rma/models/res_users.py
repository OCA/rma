# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2016 Vauxoo
#    Coded by: Yanina Aular <yani@vauxoo.com>
#    Planned by: Yanina Aular <yani@vauxoo.com>
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


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.constrains("rma_warehouse_id")
    def _check_edited_by_rma_manager(self):
        """ The rma_warehouse_id field can only be edited
        by group_rma_manager
        """
        group_rma_manager = self.env.ref(
            "crm_claim_rma.group_rma_manager")
        if self.env.user not in group_rma_manager.users:
            raise ValidationError(
                _("The rma_warehouse_id can only be edited"
                    " by the group RMA {group}".format(
                        group=group_rma_manager.name)))

    rma_warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="RMA Warehouse",
        help="The warehouse where the user is physically located,"
        " this field will be used for fill the warehouse field in the"
        " claims created by this user, i.e, the locations of this"
        " warehouse, will be used for the pickings of the claim")
