# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # RMAs that were created from a sale order
    rma_ids = fields.One2many(
        comodel_name='rma',
        inverse_name='order_id',
        string='RMAs',
        copy=False,
    )
    rma_count = fields.Integer(
        string='RMA count',
        compute='_compute_rma_count',
    )

    def _compute_rma_count(self):
        rma_data = self.env['rma'].read_group(
            [('order_id', 'in', self.ids)], ['order_id'], ['order_id'])
        mapped_data = dict(
            [(r['order_id'][0], r['order_id_count']) for r in rma_data])
        for record in self:
            record.rma_count = mapped_data.get(record.id, 0)

    def action_create_rma(self):
        self.ensure_one()
        if self.state not in ['sale', 'done']:
            raise ValidationError(_("You may only create RMAs from a "
                                    "confirmed or done sale order."))
        wizard_obj = self.env['sale.order.rma.wizard']
        line_vals = [(0, 0, {
            'product_id': data['product'].id,
            'quantity': data['quantity'],
            'uom_id': data['uom'].id,
            'picking_id': data['picking'] and data['picking'].id,
        }) for data in self.get_delivery_rma_data()]
        wizard = wizard_obj.with_context(active_id=self.id).create({
            'line_ids': line_vals,
            'location_id': self.warehouse_id.rma_loc_id.id
        })
        return {
            'name': _('Create RMA'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order.rma.wizard',
            'res_id': wizard.id,
            'target': 'new',
        }

    def action_view_rma(self):
        self.ensure_one()
        action = self.env.ref('rma.rma_action').read()[0]
        rma = self.rma_ids
        if len(rma) == 1:
            action.update(
                res_id=rma.id,
                view_mode="form",
            )
        else:
            action['domain'] = [('id', 'in', rma.ids)]
        return action

    def get_delivery_rma_data(self):
        self.ensure_one()
        data = []
        for line in self.order_line:
            data += line.prepare_sale_rma_data()
        return data

    def get_portal_delivery_rma_data(self):
        self.ensure_one()
        data = []

        rma_product = self.rma_ids.mapped('product_id')
        for line in self.order_line.filtered(
                lambda r: r.product_id not in rma_product):
            data += line.prepare_sale_rma_data()
        return data


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def get_delivery_move(self):
        self.ensure_one()
        return self.move_ids.filtered(lambda r: (
            self.product_id == r.product_id
            and r.state == 'done'
            and not r.scrapped
            and r.location_dest_id.usage == "customer"
            and (not r.origin_returned_move_id
                 or (r.origin_returned_move_id and r.to_refund))
        ))

    def prepare_sale_rma_data(self):
        self.ensure_one()
        product = self.product_id
        if self.product_id.type != 'product':
            return {}
        moves = self.get_delivery_move()
        data = []
        if moves:
            for move in moves:
                qty = move.product_uom_qty
                move_dest = move.move_dest_ids.filtered(
                    lambda r: r.state in ['partially_available',
                                          'assigned', 'done'])
                qty -= sum(move_dest.mapped('product_uom_qty'))
                data.append({
                    'product': product,
                    'quantity': qty,
                    'uom': move.product_uom,
                    'picking': move.picking_id,
                })
        else:
            data.append({
                'product': product,
                'quantity': self.qty_delivered,
                'uom': self.product_uom,
                'picking': False,
            })
        return data
