# -*- encoding: utf-8 -*-
###############################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://www.vauxoo.com>).
#    All Rights Reserved
# ############ Credits ########################################################
#    Coded by: Yanina Aular <yanina.aular@vauxoo.com>
#    Planified by: Yanina Aular <yanina.aular@vauxoo.com>
#    Audited by: Nhomar Hernandez <nhomar@vauxoo.com>
###############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from openerp import models, fields, api


class stock_production_lot(models.Model):

    _inherit = 'stock.production.lot'

    supplier_id = fields.Many2one('res.partner', string='Supplier',
                                  help="Supplier of good in claim")

    def default_get(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        res = super(stock_production_lot,
                    self).default_get(cr, uid, fields_list, context=context)
        transfer_item_id = context.get('active_id', False)

        if transfer_item_id:
            picking = self.pool.\
                get('stock.transfer_details_items').browse(cr,
                                                           uid,
                                                           transfer_item_id,
                                                           context=context)
            partner_id = picking.transfer_id.picking_id.partner_id
            if partner_id:
                res.update({'supplier_id': partner_id.id})
        return res


class stock_transfer_details(models.TransientModel):

    _inherit = 'stock.transfer_details'

    @api.one
    def do_detailed_transfer(self):
        """
        When make transfer of incoming type, and stock move have serial/lot
        number, the supplier is assigned in serial/lot number, take from
        picking.
        """
        stock_prod = self.env['stock.production.lot']
        stock_picking = self.env['stock.picking']
        picking_brw = stock_picking.browse(self.picking_id.id)
        if picking_brw.picking_type_id.code == 'incoming':
            for lstits in [self.item_ids, self.packop_ids]:
                for prod in lstits:
                    if prod.lot_id:
                        stock_prod_brw = stock_prod.browse(prod.lot_id.id)
                        if not stock_prod_brw.supplier_id:
                            stock_prod_brw.write({'supplier_id':
                                                  picking_brw.partner_id.id})
        super(stock_transfer_details, self).do_detailed_transfer()
        return True
