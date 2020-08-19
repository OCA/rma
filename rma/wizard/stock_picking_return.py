# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    create_rma = fields.Boolean(
        string="Create RMAs"
    )
    picking_type_code = fields.Selection(
        selection=[
            ('incoming', 'Vendors'),
            ('outgoing', 'Customers'),
            ('internal', 'Internal'),
        ],
        related='picking_id.picking_type_id.code',
        store=True,
        readonly=True,
    )

    @api.onchange("create_rma")
    def _onchange_create_rma(self):
        if self.create_rma:
            warehouse = self.picking_id.picking_type_id.warehouse_id
            self.location_id = warehouse.rma_loc_id.id
            rma_loc = warehouse.search([]).mapped('rma_loc_id')
            rma_loc_domain = [('id', 'child_of', rma_loc.ids)]
        else:
            self.location_id = self.default_get(['location_id'])['location_id']
            rma_loc_domain = [
                '|',
                ('id', '=', self.picking_id.location_id.id),
                ('return_location', '=', True),
            ]
        return {'domain': {'location_id': rma_loc_domain}}

    def create_returns(self):
        """ Override create_returns method for creating one or more
        'confirmed' RMAs after return a delivery picking in case
        'Create RMAs' checkbox is checked in this wizard.
        New RMAs will be linked to the delivery picking as the origin
        delivery and also RMAs will be linked to the returned picking
        as the 'Receipt'.
        """
        if self.create_rma:
            # set_rma_picking_type is to override the copy() method of stock
            # picking and change the default picking type to rma picking type
            self_with_context = self.with_context(set_rma_picking_type=True)
            res = super(ReturnPicking, self_with_context).create_returns()
            if not self.picking_id.partner_id:
                raise ValidationError(_(
                    "You must specify the 'Customer' in the "
                    "'Stock Picking' from which RMAs will be created"))
            returned_picking = self.env['stock.picking'].browse(res['res_id'])
            vals_list = [move._prepare_return_rma_vals(self.picking_id)
                         for move in returned_picking.move_lines]
            self.env['rma'].create(vals_list)
            return res
        else:
            return super().create_returns()
