# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Benoît GUILLOT <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class ClaimLine(models.Model):
    _inherit = 'claim.line'

    move_loss_id = fields.Many2one(
        'stock.move', string='Move Line from picking to loss location',
        help='The move line related to the lost product')
