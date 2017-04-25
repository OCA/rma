# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp import api, fields, models


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    rma_line_id = fields.Many2one('rma.order.line', 'RMA')

    @api.model
    def _run_move_create(self, procurement):
        res = super(ProcurementOrder, self)._run_move_create(procurement)
        if procurement.rma_line_id:
            line = procurement.rma_line_id
            if line.partner_address_id:
                res['partner_id'] = line.partner_address_id.id
            elif line.invoice_line_id.invoice_id.partner_id:
                res['partner_id'] = line.invoice_id.partner_id.id
        return res


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    rma_id = fields.Many2one('rma.order', 'RMA')
