# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def action_assign(self):
        for picking in self:
            for move in picking.move_lines:
                if len(move.rma_id):
                    if move.state in ('confirmed', 'waiting', 'assigned') \
                            and move.location_id.usage in (
                                'supplier', 'customer'):
                        move.force_assign()
        return super(StockPicking, self).action_assign()


class StockMove(models.Model):

    _inherit = "stock.move"

    rma_id = fields.Many2one('rma.order.line', string='RMA',
                             ondelete='restrict')

    @api.model
    def _prepare_picking_assign(self, move):
        res = super(StockMove, self)._prepare_picking_assign(move)
        if 'rma' in self.env.context:
            res['rma_id'] = self.env.context['rma']
        return res
