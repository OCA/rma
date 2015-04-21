# -*- coding: utf-8 -*-
##############################################################################
#
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
from openerp import models, fields, api, _
from openerp.exceptions import except_orm
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp import workflow
import time


class claim_make_picking(models.TransientModel):

    _name = 'claim_make_picking.wizard'
    _description = 'Wizard to create pickings from claim lines'

    @api.model
    def _get_picking_type(self, picking_type_xml_id):
        picking_type_obj = self.env['stock.picking.type']
        ir_model_data = self.env['ir.model.data']

        picking_type_id = ir_model_data.\
            get_object_reference(picking_type_xml_id.rpartition('.')[0],
                                 picking_type_xml_id.rpartition('.')[2])

        if picking_type_id:
            picking_type_id = picking_type_id[1]
            picking_type_rec = picking_type_obj.browse(picking_type_id)
        else:
            return False

        return picking_type_rec

    @api.model
    def _get_claim_lines(self):
        # TODO use custom states to show buttons of this wizard or not instead
        # of raise an error
        context = self._context
        line_obj = self.env['claim.line']

        picking_type = context.get('picking_type')
        picking_obj = self.env['stock.picking.type']

        good_lines = []
        line_ids = line_obj.search(
            [('claim_id', '=', context['active_id'])])

        for line in line_ids:
            # TODO fix code, be careful
            if isinstance(picking_type, int):
                pick_t = picking_obj.browse(picking_type)
                if pick_t.code == 'outgoing':
                    pick = 'out'
                else:
                    pick = 'in'
            else:
                if picking_type in ('new_delivery'):
                    pick = 'out'
                else:
                    pick = 'in'

            if pick == 'out':
                if not line.move_out_id or line.move_out_id.state == 'cancel':
                    good_lines.append(line.id)
            else:
                if not line.move_in_id or line.move_in_id.state == 'cancel':
                    good_lines.append(line.id)

        if not good_lines:
            raise except_orm(
                _('Error'),
                _('A picking has already been created for this claim.'))
        return good_lines

    # Get default source location
    @api.model
    def _get_source_loc(self):
        loc_id = False
        context = self._context
        warehouse_obj = self.env['stock.warehouse']
        partner_obj = self.env['res.partner']

        if context.get('partner_id'):
            partner_rec = partner_obj.\
                browse(context.get('partner_id'))

        if context.get('warehouse_id'):
            warehouse_rec = warehouse_obj.\
                browse(context.get('warehouse_id'))

        picking_type = context.get('picking_type')

        # TODO no se puede devolver un booleano
        if picking_type:
            if picking_type == 'new_delivery':
                loc_id = warehouse_rec.lot_stock_id
            elif partner_rec:
                loc_id = partner_rec.property_stock_customer

        return loc_id

    @api.model
    def _get_common_dest_location_from_line(self, line_ids):
        """Return the ID of the common location between all lines. If no common
        destination was  found, return False"""
        # TODO no puede retornar un booleano
        loc_id = False

        line_location = [line.location_dest_id for line in line_ids]
        line_location = list(set(line_location))
        if len(line_location) == 1:
            loc_id = line_location[0]
        return loc_id

    @api.v7
    def _get_common_partner_from_line(self, cr, uid, line_ids, context):
        """Return the ID of the common partner between all lines. If no common
        partner was found, return False"""
        partner_id = False
        line_obj = self.pool.get('claim.line')
        line_partner = []
        for line in line_obj.browse(cr, uid, line_ids, context=context):
            if (line.location_dest_id.id not in line_partner):
                line_partner.append(line.location_dest_id.id)
        # TODO FIX ME, as do when the lines have different directions
        if len(line_partner) == 1:
            partner_id = line_partner[0]
        return partner_id

    # Get default destination location
    @api.model
    def _get_dest_loc(self):
        """Return the location_id to use as destination.
        If it's an outoing shippment: take the customer stock property
        If it's an incoming shippment take the location_dest_id common to all
        lines, or if different, return None."""
        context = self._context

        loc_id = False
        partner_obj = self.env['res.partner']
        picking_obj = self.env['stock.picking.type']
        picking_type = context.get('picking_type')

        if context.get('partner_id'):
            partner_rec = partner_obj.browse(context.get('partner_id'))

        # TODO FIX ME
        if isinstance(picking_type, int):
            pick_t = picking_obj.browse(picking_type)
            loc_id = pick_t.default_location_dest_id.id
        else:
            if picking_type == 'new_delivery':
                loc_id = partner_rec.property_stock_customer
            elif picking_type == 'new_rma':
                line_ids = self._get_claim_lines()
                loc_id = self._get_common_dest_location_from_line(line_ids)
        return loc_id

    claim_line_source_location = fields.Many2one(
        'stock.location',
        string='Source Location',
        default=_get_source_loc,
        help="Location where the returned products are from.")

    claim_line_dest_location = fields.Many2one(
        'stock.location',
        string='Dest. Location',
        default=_get_dest_loc,
        help="Location where the system will stock the"
        " returned products.")

    claim_line_ids = fields.Many2many(
        'claim.line',
        'claim_line_picking',
        'claim_picking_id',
        'claim_line_id',
        default=_get_claim_lines,
        string='Claim lines')

    @api.v7
    def action_cancel(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

    # If "Create" button pressed
    def action_create_picking(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        view_obj = self.pool.get('ir.ui.view')
        picking_obj = self.pool.get('stock.picking')
        warehouse_obj = self.pool.get('stock.warehouse')

        picking_type_obj = self.pool.get('stock.picking.type')
        picking_type = context.get('picking_type')

        name = 'RMA picking out'

        if isinstance(picking_type, int):
            pick_t = picking_type_obj.browse(cr,
                                             uid,
                                             picking_type,
                                             context=context)
            if pick_t.code == 'outgoing':
                pick = 'out'
            else:
                pick = 'in'
        else:
            if picking_type in ('new_rma'):
                pick = 'in'
            else:
                pick = 'out'

        wh_rec = warehouse_obj.browse(cr,
                                      uid,
                                      context.get('warehouse_id'),
                                      context=context)
        if pick == 'out':
            pick_type = wh_rec.rma_out_type_id
            write_field = 'move_out_id'
            note = 'RMA picking out'
        else:
            pick_type = wh_rec.rma_in_type_id
            write_field = 'move_in_id'
            note = 'RMA picking ' + str(context.get('picking_type'))
            name = note

        model = 'stock.picking'
        view_id = view_obj.search(cr, uid,
                                  [('model', '=', model),
                                   ('type', '=', 'form'),
                                   ],
                                  context=context)[0]
        wizard = self.browse(cr, uid, ids[0], context=context)
        claim = self.pool.get('crm.claim').browse(cr, uid,
                                                  context['active_id'],
                                                  context=context)
        partner_id = claim.delivery_address_id.id

        claim_line_obj = self.pool.get('claim.line')
        lines_rec = [claim_line_obj.browse(cr, uid, x.id)
                     for x in wizard.claim_line_ids]
        line_ids = [x.id for x in wizard.claim_line_ids]
        # In case of product return, we don't allow one picking for various
        # product if location are different
        # or if partner address is different
        if context.get('product_return'):
            common_dest_loc_id = self._get_common_dest_location_from_line(
                cr, uid, lines_rec, context=context)
            if not common_dest_loc_id:
                raise except_orm(
                    _('Error !'),
                    _('A product return cannot be created for various '
                      'destination locations, please choose line with a '
                      'same destination location.'))
            self.pool.get('claim.line').auto_set_warranty(cr, uid,
                                                          line_ids,
                                                          context=context)

            common_dest_partner_id = self._get_common_partner_from_line(
                cr, uid, line_ids, context=context)
            if not common_dest_partner_id:
                raise except_orm(
                    _('Error !'),
                    _('A product return cannot be created for various '
                      'destination addresses, please choose line with a '
                      'same address.'))
            partner_id = common_dest_partner_id
        # create picking
        picking_id = picking_obj.create(
            cr, uid,
            {'origin': claim.number,
             'picking_type_id': pick_type.id,
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
             },
            context=context)
        # Create picking lines
        for wizard_claim_line in wizard.claim_line_ids:
            move_obj = self.pool.get('stock.move')
            move_id = move_obj.create(
                cr, uid,
                {'name': wizard_claim_line.product_id.name_template,
                 'priority': '0',
                 'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                 'date_expected':
                 time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                 'product_id': wizard_claim_line.product_id.id,
                 'product_uom': wizard_claim_line.product_id.uom_id.id,
                 'partner_id': partner_id,
                 # 'prodlot_id': wizard_claim_line.prodlot_id.id,
                 # 'product_qty': wizard_claim_line.product_returned_quantity,
                 'product_uom_qty':
                 wizard_claim_line.product_returned_quantity,
                 'picking_id': picking_id,
                 'state': 'draft',
                 'price_unit': wizard_claim_line.unit_sale_price,
                 'company_id': claim.company_id.id,
                 'location_id': wizard.claim_line_source_location.id,
                 'location_dest_id': wizard.claim_line_dest_location.id,
                 'note': note,
                 },
                context=context)
            self.pool.get('claim.line').write(
                cr, uid, wizard_claim_line.id,
                {write_field: move_id}, context=context)
        wf_service = workflow
        if picking_id:
            wf_service.trg_validate(uid, 'stock.picking',
                                    picking_id, 'button_confirm', cr)
            picking_obj.action_assign(cr, uid, [picking_id])
        domain = ("[('picking_type_id', '=', %s), ('partner_id', '=', %s)]" %
                  (pick_type.id, partner_id))
        return {
            'name': '%s' % name,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'domain': domain,
            'res_model': model,
            'res_id': picking_id,
            'type': 'ir.actions.act_window',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
