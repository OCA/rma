# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Copyright (C) 2009-2012  Akretion
#    Author: Emmanuel Samyn, Benoît GUILLOT <benoit.guillot@akretion.com>,
#            Osval Reyes
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

from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp import workflow
import time


class ClaimMakePickingFromPicking(models.TransientModel):

    _name = 'claim.make.picking.from.picking.wizard'
    _description = 'Wizard to create pickings from picking lines'

    @api.model
    def _get_default_warehouse(self):
        warehouse_id = self.env['crm.claim']._get_default_warehouse()
        return warehouse_id

    @api.model
    def _get_picking_lines(self):
        move_lines = self.env['stock.picking'].\
            browse(self.env.context.get('active_id')).move_lines
        return [mov.id for mov in move_lines]

    @api.model
    def _get_source_loc(self):
        """
        Get default source location
        """
        warehouse_id = self._get_default_warehouse()
        picking_obj = self.env['stock.picking']
        picking_id = self.env.context.get('active_id')
        picking_rec = picking_obj.browse(picking_id)
        if picking_rec.location_dest_id:
            return picking_rec.location_dest_id.id
        else:
            return warehouse_id.lot_rma_id.id

    @api.model
    def _get_dest_loc(self):
        """
        Get default destination location
        """
        warehouse_id = self._get_default_warehouse()
        loc_id = self.env['stock.location']
        picking_type = self.env.context.get('picking_type')
        picking_type_obj = self.env['stock.picking.type']

        if isinstance(picking_type, int):
            pick_t = picking_type_obj.browse(picking_type)
            loc_id = pick_t.default_location_dest_id
        else:
            if picking_type == 'picking_stock':
                loc_id = warehouse_id.lot_stock_id.id

            if picking_type == 'picking_loss':
                loc_id = warehouse_id.loss_loc_id.id

            if picking_type == 'picking_refurbish':
                loc_id = warehouse_id.lot_refurbish_id.id
        return loc_id

    picking_line_source_location = fields.Many2one(
        'stock.location', 'Source Location',
        help="Source location where the returned products are",
        required=True, default=_get_source_loc)
    picking_line_dest_location = fields.Many2one(
        'stock.location', 'Dest. Location',
        help="Target location to send returned products",
        required=True, default=_get_dest_loc)
    picking_line_ids = fields.Many2many(
        'stock.move', 'claim_picking_line_picking', 'claim_picking_id',
        'picking_line_id', 'Picking lines', default=_get_picking_lines)

    @api.multi
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_create_picking_from_picking(self):
        """
        If "Create" button pressed
        """
        picking_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        view_obj = self.env['ir.ui.view']

        if self.env.context.get('picking_type'):
            context_type = self.env.context.get('picking_type')[8:]
            note = 'Internal picking from RMA to %s' % context_type
            name = 'Internal picking to %s' % context_type
        view_id = view_obj.search([
            ('model', '=', 'stock.picking'),
            ('type', '=', 'form'),
            ('name', '=', 'stock.picking.form')
        ])[0]
        prev_picking = picking_obj.browse(self.env.context.get('active_id'))
        partner_id = prev_picking.partner_id.id
        # create picking
        picking_id = picking_obj.create({
            'origin': prev_picking.origin,
            'move_type': 'one',
            'state': 'draft',
            'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'partner_id': prev_picking.partner_id.id,
            'invoice_state': "none",
            'company_id': prev_picking.company_id.id,
            'location_id': self.picking_line_source_location.id,
            'location_dest_id': self.picking_line_dest_location.id,
            'note': note,
            'claim_id': prev_picking.claim_id.id,
            'picking_type_id': prev_picking.claim_id.warehouse_id.id,
        })

        # Create picking lines
        for wizard_picking_line in self.picking_line_ids:
            move_id = move_obj.create({
                'name': wizard_picking_line.product_id.name_template,
                'priority': '0',
                'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'date_expected': time.strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT),
                'product_id': wizard_picking_line.product_id.id,
                'product_uom_qty': wizard_picking_line.product_uom_qty,
                'product_uom': wizard_picking_line.product_uom.id,
                'partner_id': prev_picking.partner_id.id,
                'picking_id': picking_id.id,
                'state': 'draft',
                'price_unit': wizard_picking_line.price_unit,
                'company_id': prev_picking.company_id.id,
                'location_id': self.picking_line_source_location.id,
                'location_dest_id': self.picking_line_dest_location.id,
                'note': note,
                'invoice_state': 'none',
            })
            wizard_picking_line.write(
                {'move_dest_id': move_id.id})
        wf_service = workflow
        if picking_id:
            wf_service.trg_validate(
                self._uid, 'stock.picking',
                picking_id.id,
                'button_confirm',
                self._cr)
            picking_id.action_assign()
        domain = "[('picking_type_id','=','%s'),('partner_id','=',%s)]" % (
            prev_picking.claim_id.warehouse_id.rma_int_type_id.id, partner_id)
        return {
            'name': '%s' % name,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id.id,
            'domain': domain,
            'res_model': 'stock.picking',
            'res_id': picking_id.id,
            'type': 'ir.actions.act_window',
        }
