# -*- coding: utf-8 -*-
#########################################################################
#                                                                       #
#                                                                       #
#########################################################################
#                                                                       #
# crm_claim_rma for OpenERP                                             #
# Copyright (C) 2009-2012  Akretion, Emmanuel Samyn,                    #
#       Benoît GUILLOT <benoit.guillot@akretion.com>                    #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

from osv import fields, osv
import time
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import netsvc
from tools.translate import _


class claim_make_picking(osv.osv_memory):
    _name='claim_make_picking.wizard'
    _description='Wizard to create pickings from claim lines'
    _columns = {
        'claim_line_source_location' : fields.many2one('stock.location', 'Source Location',help="Location where the returned products are from.", required=True),
        'claim_line_dest_location' : fields.many2one('stock.location', 'Dest. Location',help="Location where the system will stock the returned products.", required=True),
        'claim_line_ids' : fields.many2many('claim.line', 'claim_line_picking', 'claim_picking_id', 'claim_line_id', 'Claim lines'),
    }

    def _get_claim_lines(self, cr, uid, context):
        #TODO use custom states to show buttons of this wizard or not instead of raise an error
        if context is None: context = {}
        line_obj = self.pool.get('claim.line')
        if context.get('picking_type') in ['in', 'loss']:
            move_field = 'move_in_id'
        elif context.get('picking_type') == 'out':
            move_field = 'move_out_id'
        good_lines = []
        line_ids =  line_obj.search(cr, uid, [('claim_id', '=', context['active_id'])], context=context)
        for line in line_obj.browse(cr, uid, line_ids, context=context):
            if not line[move_field] or line[move_field].state == 'cancel':
                good_lines.append(line.id)
        if not good_lines:
            raise osv.except_osv(_('Error !'), _('A picking has already been created for this claim !'))
        return good_lines

    # Get default source location
    def _get_source_loc(self, cr, uid, context):
        if context is None: context = {}
        warehouse_obj = self.pool.get('stock.warehouse')
        warehouse_id = context.get('warehouse_id')
        if context.get('picking_type') == 'out':
            loc_id = warehouse_obj.read(cr, uid, warehouse_id, ['lot_stock_id'], context=context)['lot_stock_id'][0]
        elif context.get('picking_type') in ['in', 'loss'] and context.get('partner_id'):
            loc_id = self.pool.get('res.partner').read(cr, uid, context['partner_id'],
                                              ['property_stock_customer'],
                                              context=context)['property_stock_customer']
        return loc_id

    # Get default destination location
    def _get_dest_loc(self, cr, uid, context):
        if context is None: context = {}
        warehouse_obj = self.pool.get('stock.warehouse')
        warehouse_id = context.get('warehouse_id')
        if context.get('picking_type') == 'out':
            loc_id = self.pool.get('res.partner').read(cr, uid, context.get('partner_id'), ['property_stock_customer'], context=context)['property_stock_customer'][0]
        elif context.get('picking_type') == 'in':
            loc_id = warehouse_obj.read(cr, uid, warehouse_id, ['lot_rma_id'], context=context)['lot_rma_id'][0]
        elif context.get('picking_type') == 'loss':
            loc_id = warehouse_obj.read(cr, uid, warehouse_id, ['lot_carrier_loss_id'], context=context)['lot_carrier_loss_id'][0]
        return loc_id

    _defaults = {
        'claim_line_source_location': _get_source_loc,
        'claim_line_dest_location': _get_dest_loc,
        'claim_line_ids': _get_claim_lines,
    }

    def action_cancel(self,cr,uid,ids,conect=None):
        return {'type': 'ir.actions.act_window_close',}

    # If "Create" button pressed
    def action_create_picking(self, cr, uid, ids, context=None):
        picking_obj = self.pool.get('stock.picking')
        if context is None: context = {}
        view_obj = self.pool.get('ir.ui.view')
        claim_picking = False
        if context.get('picking_type') in ['in', 'loss']:
            p_type = 'in'
            view_xml_id = 'stock_picking_form'
            view_name = 'stock.picking.form'
            write_field = 'move_in_id'
            if context.get('picking_type') == 'in':
                claim_picking = True
                note = 'RMA picking in'
                name = 'Customer picking in'
            elif context.get('picking_type') == 'loss':
                name = 'Customer product loss'
                note = 'RMA product loss'
        elif context.get('picking_type') == 'out':
            p_type = 'out'
            write_field = 'move_out_id'
            note = 'RMA picking out'
            name = 'Customer picking out'
            view_xml_id = 'stock_picking_form'
            view_name = 'stock.picking.form'
        view_id = view_obj.search(cr, uid, [
                                            ('xml_id', '=', view_xml_id),
                                            ('model', '=', 'stock.picking'),
                                            ('type', '=', 'form'),
                                            ('name', '=', view_name)
                                            ], context=context)[0]
        wizard = self.browse(cr, uid, ids[0], context=context)
        claim = self.pool.get('crm.claim').browse(cr, uid, context['active_id'], context=context)
        partner_id = claim.partner_id.id
        # create picking
        picking_id = picking_obj.create(cr, uid, {
                    'origin': claim.number,
                    'type': p_type,
                    'move_type': 'one', # direct
                    'state': 'draft',
                    'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'partner_id': claim.partner_id.id,
                    'invoice_state': "none",
                    'company_id': claim.company_id.id,
                    'location_id': wizard.claim_line_source_location.id,
                    'location_dest_id': wizard.claim_line_dest_location.id,
                    'note' : note,
                    'claim_id': claim.id,
                    'claim_picking': claim_picking
                })
        # Create picking lines
        for wizard_claim_line in wizard.claim_line_ids:
            move_id = self.pool.get('stock.move').create(cr, uid, {
                    'name' : wizard_claim_line.product_id.name_template, # Motif : crm id ? stock_picking_id ?
                    'priority': '0',
                    #'create_date':
                    'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'date_expected': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'product_id': wizard_claim_line.product_id.id,
                    'product_qty': wizard_claim_line.product_returned_quantity,
                    'product_uom': wizard_claim_line.product_id.uom_id.id,
                    'partner_id': claim.partner_id.id,
                    'prodlot_id': wizard_claim_line.prodlot_id.id,
                    # 'tracking_id':
                    'picking_id': picking_id,
                    'state': 'draft',
                    'price_unit': wizard_claim_line.unit_sale_price,
                    # 'price_currency_id': claim_id.company_id.currency_id.id, # from invoice ???
                    'company_id': claim.company_id.id,
                    'location_id': wizard.claim_line_source_location.id,
                    'location_dest_id': wizard.claim_line_dest_location.id,
                    'note': note,
                })
            self.pool.get('claim.line').write(cr, uid, wizard_claim_line.id, {write_field: move_id}, context=context)
        wf_service = netsvc.LocalService("workflow")
        if picking_id:
            wf_service.trg_validate(uid, 'stock.picking', picking_id,'button_confirm', cr)
            picking_obj.action_assign(cr, uid, [picking_id])
        return {
            'name': '%s' % name,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'domain' : "[('type', '=', '%s'),('partner_id','=',%s)]" % (p_type, partner_id),
            'res_model': 'stock.picking',
            'res_id': picking_id,
            'type': 'ir.actions.act_window',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
