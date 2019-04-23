# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    warranty_exp_date = fields.Date(string='Warranty Expiration Date')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.warranty_exp_date = False
        if self.product_id and \
                self.product_id.product_tmpl_id.warranty_type and \
                self.product_id.product_tmpl_id.warranty:
            warranty_type = self.product_id.product_tmpl_id.warranty_type
            if warranty_type == 'day':
                time = (datetime.now() +
                        timedelta(days=self.product_id.
                                  product_tmpl_id.warranty)).strftime(
                    DEFAULT_SERVER_DATE_FORMAT)
            elif warranty_type == 'week':
                time = (datetime.now() +
                        timedelta(weeks=self.product_id.
                                  product_tmpl_id.warranty)).strftime(
                    DEFAULT_SERVER_DATE_FORMAT)
            elif warranty_type == 'month':
                time = (datetime.now() +
                        relativedelta(months=+self.product_id.
                                      product_tmpl_id.warranty)).strftime(
                    DEFAULT_SERVER_DATE_FORMAT)
            elif warranty_type == 'year':
                time = (datetime.now() +
                        relativedelta(years=+self.product_id.
                                      product_tmpl_id.warranty)).strftime(
                    DEFAULT_SERVER_DATE_FORMAT)
            self.warranty_exp_date = time
