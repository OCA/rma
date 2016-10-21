# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Eezee-It, MONK Software
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume, Leonardo Donelli
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
import time

from openerp import models, fields, exceptions, api, _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT


class ClaimMakePicking(models.TransientModel):
    _name = 'claim_make_picking.wizard'
    _description = 'Wizard to create pickings from claim lines'

    @api.returns('stock.location')
    def _get_common_dest_location_from_line(self, lines):
        """If all the lines have the same destination location return that,
        else return an empty recordset
        """
        location = self.env['stock.location']
        location_ids = list(set(lines.mapped('location_dest_id')))
        return location_ids[0] if len(location_ids) == 1 else location

    @api.returns('res.partner')
    def _get_common_partner_from_line(self, lines):
        """If all the lines have the same warranty return partner return that,
        else return an empty recordset
        """
        partner = self.env['res.partner']
        partner_ids = list(set(lines.mapped('warranty_return_partner')))
        return partner_ids[0] if len(partner_ids) == 1 else partner

    @api.model
    def _default_claim_line_source_location_id(self):
        picking_type = self.env.context.get('picking_type')
        partner_id = self.env.context.get('partner_id')
        warehouse_id = self.env.context.get('warehouse_id')
        claim_id = self.env.context.get('active_id')
        claim_id = self.env['crm.claim'].browse(claim_id)
        location_id = self.env['stock.location']

        if picking_type == 'in':
            location_id = claim_id.partner_id.property_stock_customer
        elif picking_type == 'out' and warehouse_id:
            location_id = self.env['stock.warehouse'].browse(
                warehouse_id).lot_stock_id
        elif partner_id:
            location_id = self.env['res.partner'].browse(partner_id).\
                property_stock_customer

        # return empty recordset, see https://github.com/odoo/odoo/issues/4384
        return location_id

    def _default_claim_line_dest_location_id(self):
        """Return the location_id to use as destination.

        If it's an outgoing shipment: take the customer stock property
        If it's an incoming shipment take the location_dest_id common to all
        lines, or if different, return None.
        """
        picking_type = self.env.context.get('picking_type')
        claim_id = self.env.context.get('active_id')
        claim_id = self.env['crm.claim'].browse(claim_id)
        location_id = self.env['stock.location']

        if isinstance(picking_type, int):
            location_id = self.env['stock.picking.type'].browse(picking_type)\
                .default_location_dest_id
        elif picking_type == 'out':
            location_id = claim_id.partner_id.property_stock_customer
        elif picking_type == 'in':
            location_id = claim_id.warehouse_id.rma_in_type_id.\
                default_location_dest_id
        elif picking_type == 'int':
            location_id = claim_id.warehouse_id.rma_int_type_id.\
                default_location_dest_id
        elif picking_type == 'loss':
            location_id = claim_id.warehouse_id.loss_loc_id

        # return empty recordset, see https://github.com/odoo/odoo/issues/4384
        return location_id

    @api.returns('claim.line')
    def _default_claim_line_ids(self):
        # TODO use custom states to show buttons of this wizard or not instead
        # of raise an error
        picking_type = self.env.context.get('picking_type')
        if isinstance(picking_type, int):
            picking_type_code = self.env['stock.picking.type'].\
                browse(picking_type).code
            picking_type = 'in' if picking_type_code == 'incoming' else 'out'
        move_field = 'move_in_id' if picking_type == 'in' else 'move_out_id'

        # Search claim lines related to the current claim with no active
        # picking moves (or not at all)
        domain = [('claim_id', '=', self.env.context['active_id']),
                  '|', (move_field, '=', False),
                  (move_field + '.state', '=', 'cancel')]

        line_ids = self.env['claim.line'].search(domain)
        if not line_ids:
            raise exceptions.Warning(_('Error'), _('A picking has already been'
                                                   ' created for this claim.'))
        return line_ids

    claim_line_source_location_id = fields.Many2one(
        'stock.location', string='Source Location', required=True,
        default=_default_claim_line_source_location_id,
        help="Location where the returned products are from.")

    claim_line_dest_location_id = fields.Many2one(
        'stock.location', string='Dest. Location', required=True,
        default=_default_claim_line_dest_location_id,
        help="Location where the system will stock the returned products.")

    claim_line_ids = fields.Many2many(
        'claim.line',
        'claim_line_picking',
        'claim_picking_id',
        'claim_line_id',
        string='Claim lines', default=_default_claim_line_ids)

    def _get_picking_name(self):
        return 'RMA picking %s' % self.env.context.get('picking_type', 'in')

    def _get_picking_note(self):
        return self._get_picking_name()

    def _get_picking_data(self, claim, picking_type, partner_id):
        return {
            'origin': claim.code,
            'picking_type_id': picking_type.id,
            'move_type': 'one',  # direct
            'state': 'draft',
            'date': time.strftime(DT_FORMAT),
            'partner_id': partner_id,
            'invoice_state': "none",
            'company_id': claim.company_id.id,
            'location_id': self.claim_line_source_location_id.id,
            'location_dest_id': self.claim_line_dest_location_id.id,
            'note': self._get_picking_note(),
            'claim_id': claim.id,
        }

    def _get_picking_line_data(self, claim, picking, line):
        return {
            'name': line.product_id.name_template,
            'priority': '0',
            'date': time.strftime(DT_FORMAT),
            'date_expected': time.strftime(DT_FORMAT),
            'product_id': line.product_id.id,
            'product_uom_qty': line.product_returned_quantity,
            'product_uom': line.product_id.product_tmpl_id.uom_id.id,
            'partner_id': claim.delivery_address_id.id,
            'picking_id': picking.id,
            'state': 'draft',
            'price_unit': line.unit_sale_price,
            'company_id': claim.company_id.id,
            'location_id': self.claim_line_source_location_id.id,
            'location_dest_id': self.claim_line_dest_location_id.id,
            'note': self._get_picking_note(),
        }

    @api.multi
    def action_create_picking(self):
        context = self.env.context
        picking_type_code = context.get('picking_type')
        warehouse = self.env['stock.warehouse']
        warehouse_id = warehouse.browse(context.get('warehouse_id'))
        if isinstance(picking_type_code, int):
            picking_obj = self.env['stock.picking.type']
            picking_type_code = picking_obj.browse(picking_type_code).code

        picking_type = warehouse_id.int_type_id
        write_field = 'move_out_id'
        if picking_type_code == 'incoming':
            picking_type = warehouse_id.in_type_id
            write_field = 'move_in_id'
        elif picking_type_code == 'outgoing':
            picking_type = warehouse_id.out_type_id

        claim_id = self.env['crm.claim'].browse(context.get('active_id'))
        partner_id = claim_id.delivery_address_id.id
        claim_line_ids = self.claim_line_ids

        # In case of product return, we don't allow one picking for various
        # product if location are different
        # or if partner address is different
        if context.get('product_return'):
            common_dest_location = self._get_common_dest_location_from_line(
                claim_line_ids)
            if not common_dest_location:
                raise exceptions.Warning(
                    _('Error'),
                    _('A product return cannot be created for '
                      'various destination locations, please choose '
                      'line with a same destination location.'))

            claim_line_ids.set_warranty()
            common_dest_partner = self._get_common_partner_from_line(
                claim_line_ids)
            if not common_dest_partner:
                raise exceptions.Warning(
                    _('Error'), _('A product return cannot be created for '
                                  'various destination addresses, please '
                                  'choose line with a same address.'))
            partner_id = common_dest_partner.id

        # create picking
        picking_id = self.env['stock.picking'].create(
            self._get_picking_data(claim_id, picking_type, partner_id))

        # Create picking lines
        for line_id in self.claim_line_ids:
            move_id = self.env['stock.move'].create(
                self._get_picking_line_data(claim_id, picking_id, line_id))
            line_id.write({write_field: move_id.id})

        if picking_id:
            picking_id.signal_workflow('button_confirm')
            picking_id.action_assign()

        domain = [('picking_type_id', '=', picking_type.id),
                  ('partner_id', '=', partner_id)]

        view_id = self.env['ir.ui.view'].search([
            ('model', '=', 'stock.picking'),
            ('type', '=', 'form')])[0]
        return {
            'name': self._get_picking_name(),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id.id,
            'domain': str(domain),
            'res_model': 'stock.picking',
            'res_id': picking_id.id,
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
