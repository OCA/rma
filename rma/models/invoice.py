# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp import api, fields, models


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    @api.one
    def _compute_rma_count(self):
        rma_list = []
        for invl in self.invoice_line_ids:
            for rmal in invl.rma_line_ids:
                rma_list.append(rmal.rma_id.id)
        self.rma_count = len(list(set(rma_list)))

    rma_count = fields.Integer(compute=_compute_rma_count,
                               string='# of RMA',
                               copy=False)

    @api.multi
    def action_view_rma_supplier(self):
        action = self.env.ref('rma.action_rma_supplier')
        result = action.read()[0]
        rma_list = []
        for invl in self.invoice_line_ids:
            for rmal in invl.rma_line_ids:
                rma_list.append(rmal.rma_id.id)
        self.rma_count = len(list(set(rma_list)))
        # choose the view_mode accordingly
        if len(rma_list) != 1:
            result['domain'] = "[('id', 'in', " + \
                               str(rma_list) + ")]"
        elif len(rma_list) == 1:
            res = self.env.ref('rma.view_rma_supplier_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = rma_list[0]
        return result

    @api.multi
    def action_view_rma(self):
        action = self.env.ref('rma.action_rma_customer')
        result = action.read()[0]
        rma_list = []
        for invl in self.invoice_line_ids:
            for rmal in invl.rma_line_ids:
                rma_list.append(rmal.rma_id.id)
        self.rma_count = len(list(set(rma_list)))
        # choose the view_mode accordingly
        if len(rma_list) != 1:
            result['domain'] = "[('id', 'in', " + \
                               str(rma_list) + ")]"
        elif len(rma_list) == 1:
            res = self.env.ref('rma.view_rma_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = rma_list[0]
        return result


class AccountInvoiceLine(models.Model):

    _inherit = "account.invoice.line"

    rma_line_ids = fields.One2many(
        comodel_name='rma.order.line', inverse_name='invoice_line_id',
        string="RMA", readonly=True,
        help="This will contain the rmas for the invoice line")

    rma_line_refund_ids = fields.One2many(
        comodel_name='rma.order.line', inverse_name='refund_line_id',
        string="RMA for refund", readonly=True,
        help="This will contain the rmas for the refund line")
