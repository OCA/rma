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
from openerp.osv import fields, orm
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp import netsvc
from openerp.tools.translate import _
import time


class claim_make_picking(orm.TransientModel):

    _name = 'claim_make_picking.wizard'
    _description = 'Wizard to create pickings from claim lines'
    _columns = {
        'claim_line_source_location': fields.many2one(
            'stock.location',
            string='Source Location',
            help="Location where the returned products are from.",
            required=True),
        'claim_line_dest_location': fields.many2one(
            'stock.location',
            string='Dest. Location',
            help="Location where the system will stock the returned products.",
            required=True),
        'claim_line_ids': fields.many2many(
            'claim.line',
            'claim_line_picking',
            'claim_picking_id',
            'claim_line_id',
            string='Claim lines'),
    }

    def _get_claim_lines(self, cr, uid, context):
        # TODO use custom states to show buttons of this wizard or not instead
        # of raise an error
        if context is None:
            context = {}
        line_obj = self.pool.get('claim.line')
        if context.get('picking_type') == 'out':
            move_field = 'move_out_id'
        else:
            move_field = 'move_in_id'
        good_lines = []
        line_ids = line_obj.search(
            cr, uid,
            [('claim_id', '=', context['active_id'])],
            context=context)
        for line in line_obj.browse(cr, uid, line_ids, context=context):
            if not line[move_field] or line[move_field].state == 'cancel':
                good_lines.append(line.id)
        if not good_lines:
            raise orm.except_orm(
                _('Error'),
                _('A picking has already been created for this claim.'))
        return good_lines

    # Get default source location
    def _get_source_loc(self, cr, uid, context):
        loc_id = False
        if context is None:
            context = {}
        warehouse_obj = self.pool.get('stock.warehouse')
        warehouse_id = context.get('warehouse_id')
        if context.get('picking_type') == 'out':
            loc_id = warehouse_obj.read(
                cr, uid, warehouse_id,
                ['lot_stock_id'],
                context=context)['lot_stock_id'][0]
        elif context.get('partner_id'):
            loc_id = self.pool.get('res.partner').read(
                cr, uid, context['partner_id'],
                ['property_stock_customer'],
                context=context)['property_stock_customer'][0]
        return loc_id

    def _get_common_dest_location_from_line(self, cr, uid, line_ids, context):
        """Return the ID of the common location between all lines. If no common
        destination was  found, return False"""
        loc_id = False
        line_obj = self.pool.get('claim.line')
        line_location = []
        for line in line_obj.browse(cr, uid, line_ids, context=context):
            if line.location_dest_id.id not in line_location:
                line_location.append(line.location_dest_id.id)
        if len(line_location) == 1:
            loc_id = line_location[0]
        return loc_id

    def _get_common_partner_from_line(self, cr, uid, line_ids, context):
        """Return the ID of the common partner between all lines. If no common
        partner was found, return False"""
        partner_id = False
        line_obj = self.pool.get('claim.line')
        line_partner = []
        for line in line_obj.browse(cr, uid, line_ids, context=context):
            if (line.warranty_return_partner
                    and line.warranty_return_partner.id
                    not in line_partner):
                line_partner.append(line.warranty_return_partner.id)
        if len(line_partner) == 1:
            partner_id = line_partner[0]
        return partner_id

    # Get default destination location
    def _get_dest_loc(self, cr, uid, context):
        """Return the location_id to use as destination.
        If it's an outoing shippment: take the customer stock property
        If it's an incoming shippment take the location_dest_id common to all
        lines, or if different, return None."""
        if context is None:
            context = {}
        loc_id = False
        if context.get('picking_type') == 'out' and context.get('partner_id'):
            loc_id = self.pool.get('res.partner').read(
                cr, uid, context.get('partner_id'),
                ['property_stock_customer'],
                context=context)['property_stock_customer'][0]
        elif context.get('picking_type') == 'in' and context.get('partner_id'):
            # Add the case of return to supplier !
            line_ids = self._get_claim_lines(cr, uid, context=context)
            loc_id = self._get_common_dest_location_from_line(cr, uid,
                                                              line_ids,
                                                              context=context)
        return loc_id

    _defaults = {
        'claim_line_source_location': _get_source_loc,
        'claim_line_dest_location': _get_dest_loc,
        'claim_line_ids': _get_claim_lines,
    }

    def action_cancel(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

    # If "Create" button pressed
    def action_create_picking(self, cr, uid, ids, context=None):
        picking_obj = self.pool.get('stock.picking')
        if context is None:
            context = {}
        view_obj = self.pool.get('ir.ui.view')
        name = 'RMA picking out'
        if context.get('picking_type') == 'out':
            p_type = 'out'
            write_field = 'move_out_id'
            note = 'RMA picking out'
        else:
            p_type = 'in'
            write_field = 'move_in_id'
            if context.get('picking_type'):
                note = 'RMA picking ' + str(context.get('picking_type'))
                name = note
        model = 'stock.picking.' + p_type
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
        line_ids = [x.id for x in wizard.claim_line_ids]
        # In case of product return, we don't allow one picking for various
        # product if location are different
        # or if partner address is different
        if context.get('product_return'):
            common_dest_loc_id = self._get_common_dest_location_from_line(
                cr, uid, line_ids, context=context)
            if not common_dest_loc_id:
                raise orm.except_orm(
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
                raise orm.except_orm(
                    _('Error !'),
                    _('A product return cannot be created for various '
                      'destination addresses, please choose line with a '
                      'same address.'))
            partner_id = common_dest_partner_id
        # create picking
        picking_id = picking_obj.create(
            cr, uid,
            {'origin': claim.number,
             'type': p_type,
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
                 'date_expected': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                 'product_id': wizard_claim_line.product_id.id,
                 'product_qty': wizard_claim_line.product_returned_quantity,
                 'product_uom': wizard_claim_line.product_id.uom_id.id,
                 'partner_id': partner_id,
                 'prodlot_id': wizard_claim_line.prodlot_id.id,
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
        wf_service = netsvc.LocalService("workflow")
        if picking_id:
            wf_service.trg_validate(uid, 'stock.picking',
                                    picking_id, 'button_confirm', cr)
            picking_obj.action_assign(cr, uid, [picking_id])
        domain = ("[('type', '=', '%s'), ('partner_id', '=', %s)]" %
                  (p_type, partner_id))
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
