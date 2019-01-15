# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    warranty_exp_date = fields.Date(string='Warranty Expiration Date')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            if (self.product_id.product_tmpl_id.warranty_type and
                    self.product_id.product_tmpl_id.warranty):
                today_date = datetime.now()
                if self.product_id.product_tmpl_id.warranty_type == 'day':
                    time = (today_date +
                            timedelta(days=self.product_id.
                                      product_tmpl_id.warranty))
                elif self.product_id.product_tmpl_id.warranty_type == 'week':
                    time = (today_date +
                            timedelta(weeks=self.product_id.
                                      product_tmpl_id.warranty))
                elif self.product_id.product_tmpl_id.warranty_type == 'month':
                    time = (today_date +
                            relativedelta(months=+self.product_id.
                                          product_tmpl_id.warranty))
                elif self.product_id.product_tmpl_id.warranty_type == 'year':
                    time = (today_date +
                            relativedelta(years=+self.product_id.
                                          product_tmpl_id.warranty))
                self.warranty_exp_date = time
