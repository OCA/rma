# -*- coding: utf-8 -*-
# © 2017 Techspawn Solutions
# © 2016 Cyril Gaudin (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    claim_id = fields.Many2one('crm.claim', 'Claim')
