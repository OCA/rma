# -*- coding: utf-8 -*-
#########################################################################
#                                                                       #
#                                                                       #
#########################################################################
#                                                                       #
# crm_claim_rma for OpenERP                                             #
# Copyright (C) 2009-2012  Akretion, Emmanuel Samyn,                    #
#       Benoît GUILLOT <benoit.guillot@akretion.com>                    #
# This program is free software: you can redistribute it and/or modify  #
# it under the terms of the GNU General Public License as published by  #
# the Free Software Foundation, either version 3 of the License, or     #
# (at your option) any later version.                                   #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
# GNU General Public License for more details.                          #
#                                                                       #
# You should have received a copy of the GNU General Public License     #
# along with this program.  If not, see <http://www.gnu.org/licenses/>. #
#########################################################################

from openerp import models, fields, api


class claim_make_picking(models.TransientModel):

    _inherit = 'claim_make_picking.wizard'

    @api.model
    def _get_dest_loc(self):
        """ Get default destination location """
        context = self._context
        warehouse_obj = self.env['stock.warehouse']
        picking_type = context.get('picking_type')
        warehouse_rec = warehouse_obj.browse(context.get('warehouse_id'))
        loc_id = self.env['stock.location']

        if picking_type and picking_type == 'carrier_loss':
            loc_id = warehouse_rec.lot_carrier_loss_id
        elif picking_type and picking_type == 'new_rma':
            loc_id = warehouse_rec.lot_rma_id
        else:
            loc_id = super(claim_make_picking, self)._get_dest_loc()

        return loc_id

    claim_line_dest_location = fields.Many2one(default=_get_dest_loc)
