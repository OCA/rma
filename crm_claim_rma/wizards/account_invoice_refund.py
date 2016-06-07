# -*- coding: utf-8 -*-
# © 2015 Vauxoo
# © 2015 Eezee-It, MONK Software
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models


class AccountInvoiceRefund(models.TransientModel):
    _inherit = "account.invoice.refund"

    def _default_description(self):
        return self.env.context.get('description', '')

    description = fields.Char(default=_default_description)

    @api.multi
    def compute_refund(self, mode='refund'):
        self.ensure_one()
        invoice_ids = self.env.context.get('invoice_ids', [])
        if invoice_ids:
            self = self.with_context(active_ids=invoice_ids)
        return super(AccountInvoiceRefund, self).compute_refund(mode=mode)
