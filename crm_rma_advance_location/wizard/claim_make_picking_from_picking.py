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
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp import workflow
import time


class claim_make_picking_from_picking(models.TransientModel):

    _name = 'claim_make_picking_from_picking.wizard'
    _description = 'Wizard to create pickings from picking lines'

    @api.model
    def _get_default_warehouse(self):
        warehouse_id = self.env['crm.claim']._get_default_warehouse()
        return warehouse_id

    @api.model
    def _get_picking_lines(self):
        context = self._context
        move_lines = self.env['stock.picking'].\
            browse(context['active_id']).move_lines
        return [mov.id for mov in move_lines]

    # Get default source location
    @api.model
    def _get_source_loc(self):
        warehouse_obj = self.env['stock.warehouse']
        warehouse_id = self._get_default_warehouse()
        return warehouse_obj.browse(warehouse_id).\
            lot_rma_id.id

    # Get default destination location
    @api.model
    def _get_dest_loc(self):
        # TODO add picking_type
        context = self._context
        warehouse_id = self._get_default_warehouse()
        warehouse_obj = self.env['stock.warehouse']
        loc_id = self.env['stock.location']
        picking_type = context.get('picking_type')
        picking_type_obj = self.env['stock.picking.type']
        # TODO not working from tests
        if isinstance(picking_type, int):
            pick_t = picking_type_obj.browse(picking_type)
            loc_id = pick_t.default_location_dest_id
        else:
            if context.get('picking_type') == 'picking_stock':
                loc_id = warehouse_obj.browse(warehouse_id).lot_stock_id.id
            if context.get('picking_type') == 'picking_breakage_loss':
                loc_id = warehouse_obj.browse(warehouse_id).\
                    lot_breakage_loss_id.id
            if context.get('picking_type') == 'picking_refurbish':
                loc_id = warehouse_obj.browse(warehouse_id).lot_refurbish_id.id
            # TODO picking_mistake_loss must be added
            # if context.get('picking_type') == 'picking_mistake_loss':
            #     loc_id = warehouse_obj.browse(warehouse_id).\
            #    lot_mistake_loss_id.id
        return loc_id

    picking_line_source_location = fields.Many2one(
        'stock.location',
        'Source Location',
        help="Location where the returned products are from.",
        required=True,
        default=_get_source_loc)

    picking_line_dest_location = fields.Many2one(
        'stock.location',
        'Dest. Location',
        help="Location where the system will stock the returned products.",
        required=True,
        default=_get_dest_loc)

    picking_line_ids = fields.Many2many(
        'stock.move',
        'claim_picking_line_picking',
        'claim_picking_id',
        'picking_line_id',
        'Picking lines',
        default=_get_picking_lines)

    @api.multi
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}

    # If "Create" button pressed
    @api.multi
    def action_create_picking_from_picking(self):
        picking_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        view_obj = self.env['ir.ui.view']
        p_type = 'internal'
        context = self._context
        if context.get('picking_type'):
            context_type = context.get('picking_type')[8:]
            note = 'Internal picking from RMA to %s' % context_type
            name = 'Internal picking to %s' % context_type
        view_id = view_obj.search([
            ('xml_id', '=', 'view_picking_form'),
            ('model', '=', 'stock.picking'),
            ('type', '=', 'form'),
            ('name', '=', 'stock.picking.form')
            ])[0]
        prev_picking = picking_obj.browse(context['active_id'])
        partner_id = prev_picking.partner_id.id
        # create picking
        # TODO create picking types
        picking_id = picking_obj.create({
            'origin': prev_picking.origin,
            'type': p_type,
            'move_type': 'one',  # direct
            'state': 'draft',
            'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'partner_id': prev_picking.partner_id.id,
            'invoice_state': "none",
            'company_id': prev_picking.company_id.id,
            'location_id': self.picking_line_source_location.id,
            'location_dest_id': self.picking_line_dest_location.id,
            'note': note,
            'claim_id': prev_picking.claim_id.id,
        })
        # Create picking lines
        for wizard_picking_line in self.picking_line_ids:
            move_id = move_obj.create({
                'name': wizard_picking_line.product_id.name_template,
                # Motif : crm id ? stock_picking_id ?
                'priority': '0',
                # 'create_date':
                'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'date_expected': time.strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT),
                'product_id': wizard_picking_line.product_id.id,
                'product_qty': wizard_picking_line.product_qty,
                'product_uom': wizard_picking_line.product_uom.id,
                'partner_id': prev_picking.partner_id.id,
                'prodlot_id': wizard_picking_line.prodlot_id.id,
                # 'tracking_id':
                'picking_id': picking_id,
                'state': 'draft',
                'price_unit': wizard_picking_line.price_unit,
                # 'price_currency_id': claim_id.company_id.currency_id.id,
                # from invoice ???
                'company_id': prev_picking.company_id.id,
                'location_id': self.picking_line_source_location.id,
                'location_dest_id': self.picking_line_dest_location.id,
                'note': note,
            })
            move_obj.write(
                wizard_picking_line.id,
                {'move_dest_id': move_id})
        wf_service = workflow
        if picking_id:
            wf_service.trg_validate(
                self.uid, 'stock.picking',
                picking_id,
                'button_confirm',
                self.cr)
            picking_obj.action_assign([picking_id])
        domain = "[('type','=','%s'),('partner_id','=',%s)]" % (
            p_type, partner_id)
        return {
            'name': '%s' % name,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'domain': domain,
            'res_model': 'stock.picking',
            'res_id': picking_id,
            'type': 'ir.actions.act_window',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
