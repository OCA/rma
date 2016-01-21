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
        """
        If all the lines have the same destination location return that,
        else return an empty recordset
        """
        dests = lines.mapped('location_dest_id')
        dests = list(set(dests))
        return dests[0] if len(dests) == 1 else self.env['stock.location']

    @api.returns('res.partner')
    def _get_common_partner_from_line(self, lines):
        """
        If all the lines have the same warranty return partner return that,
        else return an empty recordset
        """
        partners = lines.mapped('warranty_return_partner')
        partners = list(set(partners))
        return partners[0] if len(partners) == 1 else self.env['res.partner']

    @api.model
    def _default_claim_line_source_location_id(self):
        picking_type = self.env.context.get('picking_type')
        partner_id = self.env.context.get('partner_id')
        warehouse_id = self.env.context.get('warehouse_id')

        if picking_type == 'out' and warehouse_id:
            return self.env['stock.warehouse'].browse(
                warehouse_id).lot_stock_id

        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            return partner.property_stock_customer

        # return empty recordset, see https://github.com/odoo/odoo/issues/4384
        return self.env['stock.location']

    def _default_claim_line_dest_location_id(self):
        """Return the location_id to use as destination.

        If it's an outoing shipment: take the customer stock property
        If it's an incoming shipment take the location_dest_id common to all
        lines, or if different, return None.
        """
        picking_type = self.env.context.get('picking_type')
        partner_id = self.env.context.get('partner_id')

        if isinstance(picking_type, int):
            picking_obj = self.env['stock.picking.type']
            return picking_obj.browse(picking_type)\
                .default_location_dest_id

        if picking_type == 'out' and partner_id:
            return self.env['res.partner'].browse(
                partner_id).property_stock_customer

        if picking_type == 'in' and partner_id:
            # Add the case of return to supplier !
            lines = self._default_claim_line_ids()
            return self._get_common_dest_location_from_line(lines)

        # return empty recordset, see https://github.com/odoo/odoo/issues/4384
        return self.env['stock.location']

    @api.returns('claim.line')
    def _default_claim_line_ids(self):
        # TODO use custom states to show buttons of this wizard or not instead
        # of raise an error
        picking_type = self.env.context.get('picking_type')
        if isinstance(picking_type, int):
            picking_obj = self.env['stock.picking.type']
            if picking_obj.browse(picking_type).code == 'incoming':
                picking_type = 'in'
            else:
                picking_type = 'out'

        move_field = 'move_in_id' if picking_type == 'in' else 'move_out_id'
        domain = [('claim_id', '=', self.env.context['active_id'])]
        lines = self.env['claim.line'].\
            search(domain)
        if lines:
            domain = domain + ['|', (move_field, '=', False),
                               (move_field + '.state', '=', 'cancel')]
            lines = lines.search(domain)
            if not lines:
                raise exceptions.Warning(
                    _('Error'),
                    _('A picking has already been created for this claim.'))
        return lines

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
        return 'RMA picking {}'.format(
            self.env.context.get('picking_type', 'in'))

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

        context = self._context
        picking_type = self.env.context.get('picking_type')
        if isinstance(picking_type, int):
            picking_obj = self.env['stock.picking.type']
            picking_type_rec = picking_obj.browse(picking_type)
            if picking_type_rec.code == 'incoming':
                picking_type = 'in'
            elif picking_type_rec.code == 'outgoing':
                picking_type = 'out'
            else:
                picking_type = 'int'

        warehouse_obj = self.env['stock.warehouse']
        warehouse_rec = warehouse_obj.browse(context.get('warehouse_id'))
        if picking_type == 'out':
            picking_type = warehouse_rec.out_type_id
            write_field = 'move_out_id'
        elif picking_type == 'in':
            picking_type = warehouse_rec.in_type_id
            write_field = 'move_in_id'
        else:
            picking_type = warehouse_rec.int_type_id
            write_field = 'move_out_id'

        claim = self.env['crm.claim'].browse(self.env.context['active_id'])
        partner_id = claim.delivery_address_id.id
        claim_lines = self.claim_line_ids

        # In case of product return, we don't allow one picking for various
        # product if location are different
        # or if partner address is different
        if self.env.context.get('product_return'):
            common_dest_location = self._get_common_dest_location_from_line(
                claim_lines)
            if not common_dest_location:
                raise exceptions.Warning(
                    _('Error'),
                    _('A product return cannot be created for various '
                      'destination locations, please choose line with a '
                      'same destination location.'))

            claim_lines.auto_set_warranty()
            common_dest_partner = self._get_common_partner_from_line(
                claim_lines)
            if not common_dest_partner:
                raise exceptions.Warning(
                    _('Error'),
                    _('A product return cannot be created for various '
                      'destination addresses, please choose line with a '
                      'same address.'))
            partner_id = common_dest_partner.id

        # create picking
        picking = self.env['stock.picking'].create(
            self._get_picking_data(claim, picking_type, partner_id))

        # Create picking lines
        for line in self.claim_line_ids:
            move = self.env['stock.move'].create(
                self._get_picking_line_data(claim, picking, line))
            line.write({write_field: move.id})

        if picking:
            picking.signal_workflow('button_confirm')
            picking.action_assign()

        domain = ("[('picking_type_id', '=', %s), ('partner_id', '=', %s)]" %
                  (picking_type.id, partner_id))

        view_id = self.env['ir.ui.view'].search(
            [('model', '=', 'stock.picking'),
             ('type', '=', 'form')])[0]
        return {
            'name': self._get_picking_name(),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id.id,
            'domain': domain,
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
