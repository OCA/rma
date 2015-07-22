# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Eezee-It
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume
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

from openerp.models import api, TransientModel, _
from openerp.fields import Many2many, Many2one
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import Warning
from openerp import netsvc

import time


class ClaimMakePicking(TransientModel):
    _name = 'claim_make_picking.wizard'
    _description = 'Wizard to create pickings from claim lines'

    # Get default source location
    def _get_source_loc(self):
        loc_id = False
        context = self.env.context
        if context is None:
            context = {}

        warehouse_obj = self.env['stock.warehouse']
        warehouse_id = context.get('warehouse_id')
        picking_type = context.get('picking_type')
        partner_id = context.get('partner_id')
        if picking_type == 'out':
            loc_id = warehouse_obj.browse(
                warehouse_id).lot_stock_id.id
        elif partner_id:
            loc_id = self.env['res.partner'].browse(
                partner_id).property_stock_customer.id

        return loc_id

    def _get_common_dest_location_from_line(self, line_ids):
        """Return the ID of the common location between all lines. If no common
        destination was  found, return False"""
        loc_id = False
        line_obj = self.env['claim.line']
        line_location = []

        for line in line_obj.browse(line_ids):
            if line.location_dest_id.id not in line_location:
                line_location.append(line.location_dest_id.id)

        if len(line_location) == 1:
            loc_id = line_location[0]

        return loc_id

    # Get default destination location
    def _get_dest_loc(self):
        """Return the location_id to use as destination.
        If it's an outoing shippment: take the customer stock property
        If it's an incoming shippment take the location_dest_id common to all
        lines, or if different, return None."""
        context = self.env.context
        if context is None:
            context = {}

        loc_id = False
        picking_type = context.get('picking_type')
        partner_id = context.get('partner_id')
        if picking_type == 'out' and partner_id:
            loc_id = self.env['res.partner'].browse(
                partner_id).property_stock_customer.id
        elif picking_type == 'in' and partner_id:
            # Add the case of return to supplier !
            line_ids = self._get_claim_lines()
            loc_id = self._get_common_dest_location_from_line(line_ids)

        return loc_id

    def _get_claim_lines(self):
        # TODO use custom states to show buttons of this wizard or not instead
        # of raise an error
        context = self.env.context
        if context is None:
            context = {}

        line_obj = self.env['claim.line']
        if context.get('picking_type') == 'out':
            move_field = 'move_out_id'
        else:
            move_field = 'move_in_id'

        good_lines = []
        lines = line_obj.search(
            [('claim_id', '=', context['active_id'])])
        for line in lines:
            if not line[move_field] or line[move_field].state == 'cancel':
                good_lines.append(line.id)

        if not good_lines:
            raise Warning(_('Error'),
                _('A picking has already been created for this claim.'))

        return good_lines

    claim_line_source_location = Many2one(
        'stock.location', string='Source Location', required=True,
        default=_get_source_loc,
        help="Location where the returned products are from.")
    claim_line_dest_location = Many2one(
        'stock.location', string='Dest. Location', required=True,
        default=_get_dest_loc,
        help="Location where the system will stock the returned products.")
    claim_line_ids = Many2many(
        'claim.line',
        'claim_line_picking',
        'claim_picking_id',
        'claim_line_id',
        string='Claim lines', default=_get_claim_lines)

    def _get_common_partner_from_line(self, line_ids):
        """Return the ID of the common partner between all lines. If no common
        partner was found, return False"""
        partner_id = False
        line_obj = self.env['claim.line']
        line_partner = []
        for line in line_obj.browse(line_ids):
            if (line.warranty_return_partner
                    and line.warranty_return_partner.id
                    not in line_partner):
                line_partner.append(line.warranty_return_partner.id)

        if len(line_partner) == 1:
            partner_id = line_partner[0]

        return partner_id

    @api.multi
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_create_picking(self):
        picking_obj = self.env['stock.picking']
        picking_type_obj = self.env['stock.picking.type']
        context = self.env.context
        if context is None:
            context = {}

        view_obj = self.env['ir.ui.view']
        name = 'RMA picking out'
        if context.get('picking_type') == 'out':
            picking_type_code = 'outgoing'
            write_field = 'move_out_id'
            note = 'RMA picking out'
        else:
            picking_type_code = 'incoming'
            write_field = 'move_in_id'

            if context.get('picking_type'):
                note = 'RMA picking ' + str(context.get('picking_type'))
                name = note

        picking_type_id = picking_type_obj.search([
            ('code', '=', picking_type_code),
            ('default_location_dest_id', '=',
             self.claim_line_dest_location.id)], limit=1).id

        model = 'stock.picking'
        view_id = view_obj.search([
            ('model', '=', model),
            ('type', '=', 'form')], limit=1).id

        claim = self.env['crm.claim'].browse(context['active_id'])
        partner_id = claim.delivery_address_id.id
        wizard = self
        claim_lines = wizard.claim_line_ids

        # In case of product return, we don't allow one picking for various
        # product if location are different
        # or if partner address is different
        if context.get('product_return'):
            common_dest_loc_id = self._get_common_dest_location_from_line(
                claim_lines.ids)
            if not common_dest_loc_id:
                raise Warning(
                    _('Error'),
                    _('A product return cannot be created for various '
                      'destination locations, please choose line with a '
                      'same destination location.'))

            claim_lines.auto_set_warranty()
            common_dest_partner_id = self._get_common_partner_from_line(
                claim_lines.ids)

            if not common_dest_partner_id:
                raise Warning(
                    _('Error'),
                    _('A product return cannot be created for various '
                      'destination addresses, please choose line with a '
                      'same address.'))

            partner_id = common_dest_partner_id

        # create picking
        picking = picking_obj.create(
            {'origin': claim.number,
             'picking_type_id': picking_type_id,
             'move_type': 'one',  # direct
             'state': 'draft',
             'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
             'partner_id': partner_id,
             'invoice_state': "none",
             'company_id': claim.company_id.id,
             'location_id': wizard.claim_line_source_location.id,
             'location_dest_id': wizard.claim_line_dest_location.id,
             'note': note,
             'claim_id': claim.id,
             })

        # Create picking lines
        fmt = DEFAULT_SERVER_DATETIME_FORMAT
        for line in wizard.claim_line_ids:
            move_id = self.env['stock.move'].create({
                'name': line.product_id.name_template,
                'priority': '0',
                'date': time.strftime(fmt),
                'date_expected': time.strftime(fmt),
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_returned_quantity,
                'product_uom': line.product_id.product_tmpl_id.uom_id.id,
                'partner_id': partner_id,
                'prodlot_id': line.prodlot_id.id,
                'picking_id': picking.id,
                'state': 'draft',
                'price_unit': line.unit_sale_price,
                'company_id': claim.company_id.id,
                'location_id': wizard.claim_line_source_location.id,
                'location_dest_id': wizard.claim_line_dest_location.id,
                'note': note}).id

            line.write({write_field: move_id})

        wf_service = netsvc.LocalService("workflow")
        if picking:
            cr, uid = self.env.cr, self.env.uid
            wf_service.trg_validate(uid, 'stock.picking',
                                    picking.id, 'button_confirm', cr)
            picking.action_assign()
        domain = ("[('picking_type_id.code', '=', '%s'), "
                  "('partner_id', '=', %s)]" % (picking_type_code, partner_id))

        return {
            'name': '%s' % name,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'domain': domain,
            'res_model': model,
            'res_id': picking.id,
            'type': 'ir.actions.act_window',
        }
