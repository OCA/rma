# -*- coding: utf-8 -*-
# © 2017 Techspawn Solutions
# © 2015 Vauxoo: Yanina Aular <yani@vauxoo.com>, Osval Reyes <osval@vauxoo.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CrmClaimType(models.Model):
    """
        CRM Claim Type
    """
    _name = 'crm.claim.type'

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean('Active', default=True)
    description = fields.Text(translate=True)
