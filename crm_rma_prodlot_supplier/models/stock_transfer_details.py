# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Author: Yanina Aular, Osval Reyes
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

from openerp import api, models


class StockTransferDetails(models.TransientModel):

    _inherit = 'stock.transfer_details'

    @api.multi
    def do_detailed_transfer(self):
        """
        When incoming type transfer are made and stock move have serial/lot
        number, the supplier is assigned to the serial/lot number taken from
        picking.
        @return: do_detailed_transfer boolean results
        """
        prodlot = self.env['stock.production.lot']

        if self.picking_id.picking_type_id.code != 'incoming':
            return super(StockTransferDetails, self).do_detailed_transfer()

        for items_packs_ids in [self.item_ids, self.packop_ids]:
            for prod in items_packs_ids:
                lot_id = prod.lot_id
                if not lot_id:
                    continue

                if not lot_id.supplier_id:
                    lot_id.write({
                        'supplier_id': self.picking_id.partner_id.id
                    })

                for move_id in self.picking_id.move_lines:

                    if lot_id.product_id.id != move_id.product_id.id:
                        continue

                    lots = prodlot.search([
                        ('supplier_invoice_line_id',
                         'in',
                         move_id.purchase_line_id.invoice_lines.mapped('id'))
                    ])

                    if len(lots) < move_id.purchase_line_id.product_qty:

                        for inv_line in move_id.purchase_line_id.invoice_lines:
                            lots = prodlot.search([('supplier_invoice_line_id',
                                                    '=', inv_line.id)])
                            if len(lots) < inv_line.quantity and \
                                    inv_line.product_id.id == \
                                    lot_id.product_id.id:
                                lot_id.write({
                                    'supplier_invoice_line_id': inv_line.id
                                })

        return super(StockTransferDetails, self).do_detailed_transfer()
