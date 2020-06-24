# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.rma.controllers.main import PortalRma


class PortalRma(PortalRma):

    def _get_filter_domain(self, kw):
        res = super()._get_filter_domain(kw)
        if 'sale_id' in kw:
            res.append(('order_id', '=', int(kw['sale_id'])))
        return res
