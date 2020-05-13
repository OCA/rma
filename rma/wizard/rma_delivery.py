# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp


class RmaReDeliveryWizard(models.TransientModel):
    _name = 'rma.delivery.wizard'
    _description = 'RMA Delivery Wizard'

    rma_count = fields.Integer()
    type = fields.Selection(
        selection=[
            ('replace', 'Replace'),
            ('return', 'Return to customer'),
        ],
        string="Type",
        required=True,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Replace Product",
    )
    product_uom_qty = fields.Float(
        string='Product qty',
        digits=dp.get_precision('Product Unit of Measure'),
    )
    product_uom = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of measure",
    )
    scheduled_date = fields.Datetime(
        required=True,
        default=fields.Datetime.now(),
    )
    warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string='Warehouse',
        required=True,
    )

    @api.constrains('product_uom_qty')
    def _check_product_uom_qty(self):
        self.ensure_one()
        rma_ids = self.env.context.get('active_ids')
        if len(rma_ids) == 1 and self.product_uom_qty <= 0:
            raise ValidationError(_('Quantity must be greater than 0.'))

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        rma_ids = self.env.context.get('active_ids')
        rma = self.env['rma'].browse(rma_ids)
        warehouse_id = self.env['stock.warehouse'].search(
            [('company_id', '=', rma[0].company_id.id)], limit=1).id
        delivery_type = self.env.context.get('rma_delivery_type')
        product_id = False
        if len(rma) == 1 and delivery_type == 'return':
            product_id = rma.product_id.id
        product_uom_qty = 0.0
        if len(rma) == 1 and rma.remaining_qty > 0.0:
            product_uom_qty = rma.remaining_qty
        res.update(
            rma_count=len(rma),
            warehouse_id=warehouse_id,
            type=delivery_type,
            product_id=product_id,
            product_uom_qty=product_uom_qty,
        )
        return res

    @api.onchange("product_id")
    def _onchange_product_id(self):
        domain_product_uom = []
        if self.product_id:
            domain_product_uom = [
                ('category_id', '=', self.product_id.uom_id.category_id.id)
            ]
            if (not self.product_uom
                    or self.product_id.uom_id.id != self.product_uom.id):
                self.product_uom = self.product_id.uom_id
        return {'domain': {'product_uom': domain_product_uom}}

    def action_deliver(self):
        self.ensure_one()
        rma_ids = self.env.context.get('active_ids')
        rma = self.env['rma'].browse(rma_ids)
        if self.type == 'replace':
            rma.create_replace(
                self.scheduled_date,
                self.warehouse_id,
                self.product_id,
                self.product_uom_qty,
                self.product_uom,
            )
        elif self.type == 'return':
            qty = uom = None
            if self.rma_count == 1:
                qty, uom = self.product_uom_qty, self.product_uom
            rma.create_return(self.scheduled_date, qty, uom)
