# -*- coding: utf-8 -*-
# © 2017 Techspawn Solutions
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockPicking(models.Model):

    _inherit = "stock.picking"

    claim_id = fields.Many2one('crm.claim', 'Claim')
