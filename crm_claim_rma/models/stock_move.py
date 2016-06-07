# -*- coding: utf-8 -*-
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models


class StockMove(models.Model):

    _name = 'stock.move'
    _inherit = ['stock.move', 'mail.thread']

    @api.model
    def create(self, vals):
        """ In case of a wrong picking out,
        We need to create a new stock_move in a picking already open.
        To avoid having to confirm the stock_move, we override the create and
        confirm it at the creation only for this case.
        """
        move = super(StockMove, self).create(vals)
        if vals.get('picking_id'):
            picking = self.env['stock.picking'].browse(vals['picking_id'])
            if picking.claim_id and picking.picking_type_id.code == 'incoming':
                move.write({'state': 'confirmed'})
        return move
