# -*- coding: utf-8 -*-
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import _, api, exceptions, fields, models


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    def _get_default_warehouse(self):
        company_id = self.env.user.company_id.id
        wh_obj = self.env['stock.warehouse']
        wh = wh_obj.search([('company_id', '=', company_id)], limit=1)
        if not wh:
            raise exceptions.UserError(
                _('There is no warehouse for the current user\'s company.')
            )
        return wh

    def _get_picking_ids(self):
        """ Search all stock_picking associated with this claim.

        Either directly with claim_id in stock_picking or through a
        procurement_group.
        """
        picking_model = self.env['stock.picking']
        for claim in self:
            claim.picking_ids = picking_model.search([
                '|',
                ('claim_id', '=', claim.id),
                ('group_id.claim_id', '=', claim.id)
            ])

    @api.multi
    def name_get(self):
        res = []
        for claim in self:
            code = claim.code and str(claim.code) or ''
            res.append((claim.id, '[' + code + '] ' + claim.name))
        return res

    company_id = fields.Many2one(change_default=True,
                                 default=lambda self:
                                 self.env['res.company']._company_default_get(
                                     'crm.claim'))

    claim_line_ids = fields.One2many('claim.line', 'claim_id',
                                     string='Return lines')
    planned_revenue = fields.Float('Expected revenue')
    planned_cost = fields.Float('Expected cost')
    real_revenue = fields.Float()
    real_cost = fields.Float()
    invoice_ids = fields.One2many('account.invoice', 'claim_id', 'Refunds',
                                  copy=False)
    picking_ids = fields.One2many('stock.picking',
                                  compute=_get_picking_ids,
                                  string='RMA',
                                  copy=False)
    invoice_id = fields.Many2one('account.invoice', string='Invoice',
                                 help='Related original Cusotmer invoice')
    pick = fields.Boolean('Pick the product in the store')
    delivery_address_id = fields.Many2one('res.partner',
                                          string='Partner delivery address',
                                          help="This address will be used to "
                                          "deliver repaired or replacement "
                                          "products.")
    sequence = fields.Integer(default=lambda *args: 1)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
                                   required=True,
                                   default=_get_default_warehouse)
    rma_number = fields.Char(size=128, help='RMA Number provided by supplier')

    @api.model
    def _get_claim_type_default(self):
        return self.env.ref('crm_claim_type.crm_claim_type_customer')

    claim_type = \
        fields.Many2one(default=_get_claim_type_default,
                        help="Claim classification",
                        required=True)

    @api.onchange('invoice_id')
    def _onchange_invoice(self):
        # Since no parameters or context can be passed from the view,
        # this method exists only to call the onchange below with
        # a specific context (to recreate claim lines).
        # This does require to re-assign self.invoice_id in the new object
        claim_with_ctx = self.with_context(
            create_lines=True
        )
        claim_with_ctx.invoice_id = self.invoice_id
        claim_with_ctx._onchange_invoice_warehouse_type_date()
        values = claim_with_ctx._convert_to_write(claim_with_ctx._cache)
        self.update(values)

    @api.onchange('warehouse_id', 'claim_type', 'date')
    def _onchange_invoice_warehouse_type_date(self):
        context = self.env.context
        if not self.warehouse_id:
            self.warehouse_id = self._get_default_warehouse()
        create_lines = context.get('create_lines')

        if create_lines:  # happens when the invoice is changed
            self._create_claim_lines()

        if self.invoice_id:
            self.delivery_address_id = self.invoice_id.partner_id.id

    @api.model
    def __check_packages_enabled(self):
        group = self.env.ref(
            "stock.group_tracking_lot",
            raise_if_not_found=False,
        )
        employee_group = self.env.ref("base.group_user")
        # if package managing is not activated or group deleted
        if (not group or
                group.id not in employee_group.implied_ids.ids or
                not group.users):
            return False
        return True

    def _create_claim_lines(self):
        self.ensure_one()
        claim_lines = []
        # here we should check if packages are enabled
        if self.__check_packages_enabled():
            # create claim lines from invoice lines with packages
            claim_lines.extend(self.__create_lines_from_invoice_packages())
        else:
            # create claim lines from invoice lines
            claim_lines.extend(self.__create_lines_from_invoice())

        value = self._convert_to_cache(
            {'claim_line_ids': claim_lines}, validate=False)
        self.update(value)

    def __create_lines_from_invoice(self):
        claim_line = self.env['claim.line']
        warehouse = self.warehouse_id
        invoices_lines = self.invoice_id.invoice_line_ids.filtered(
            lambda line: line.product_id.type in ('consu', 'product')
        )
        lines = []
        for invoice_line in invoices_lines:
            location_dest = claim_line.get_destination_location(
                invoice_line.product_id, warehouse)
            line = {
                'name': invoice_line.name,
                'claim_origin': "none",
                'invoice_line_id': invoice_line.id,
                'product_id': invoice_line.product_id.id,
                'product_returned_quantity': invoice_line.quantity,
                'unit_sale_price': invoice_line.price_unit,
                'location_dest_id': location_dest.id,
                'state': 'draft',
            }
            line.update(invoice_line.invoice_id.warranty_values(
                invoice_line.product_id,
                self,
            ))
            lines.append((0, 0, line))
        return lines

    def __create_lines_from_invoice_packages(self):
        claim_line = self.env['claim.line']
        warehouse = self.warehouse_id
        invoices_lines = self.invoice_id.invoice_line_ids.filtered(
            lambda line: line.product_id.type in ('consu', 'product')
        )
        lines = []
        for invoice_line in invoices_lines:
            location_dest = claim_line.get_destination_location(
                invoice_line.product_id, warehouse)
            sale_line = invoice_line.sale_line_ids[0]
            # here should be only one move
            move = sale_line.procurement_ids[0].move_ids.filtered(
                lambda x: x.product_id == sale_line.product_id,
            )[0]
            for quant in move.quant_ids:
                line = {
                    'name': invoice_line.name,
                    'claim_origin': "none",
                    'invoice_line_id': invoice_line.id,
                    'product_id': invoice_line.product_id.id,
                    'product_returned_quantity': quant.qty,
                    'unit_sale_price': invoice_line.price_unit,
                    'location_dest_id': location_dest.id,
                    'state': 'draft',
                    'quant_id': quant.id,
                    'origin_move': move.id,
                }
                line.update(invoice_line.invoice_id.warranty_values(
                    invoice_line.product_id,
                    self,
                ))
                lines.append((0, 0, line))
        return lines

    @api.model
    def message_get_reply_to(self, res_ids, default=None):
        """ Override to get the reply_to of the parent project.
        """
        results = dict.fromkeys(res_ids, default or False)
        if res_ids:
            claims = self.browse(res_ids)
            results.update({
                claim.id: self.env['crm.team'].message_get_reply_to(
                    [claim.team_id], default
                )[claim.team_id] for claim in claims if claim.team_id
            })

        return results

    @api.multi
    def message_get_suggested_recipients(self):
        recipients = super(CrmClaim, self).message_get_suggested_recipients()
        try:
            for claim in self:
                if claim.partner_id:
                    claim._message_add_suggested_recipient(
                        recipients,
                        partner=claim.partner_id,
                        reason=_('Customer')
                    )
                elif claim.email_from:
                    claim._message_add_suggested_recipient(
                        recipients,
                        email=claim.email_from,
                        reason=_('Customer Email')
                    )
        except exceptions.AccessError:
            # no read access rights -> just ignore suggested recipients
            # because this imply modifying followers
            pass
        return recipients

    def _get_sequence_number(self, code_id):
        claim_type_code = self.env['crm.claim.type'].\
            browse(code_id).ir_sequence_id.code
        sequence = self.env['ir.sequence']

        return claim_type_code and sequence.next_by_code(
            claim_type_code
        ) or '/'

    @api.model
    def create(self, values):
        values = values or {}
        if 'code' not in values or not values.get('code') \
                or values.get('code') == '/':

            claim_type = values.get('claim_type')
            if not claim_type:
                claim_type = self._get_claim_type_default().id

            values['code'] = self._get_sequence_number(claim_type)

        return super(CrmClaim, self).create(values)

    @api.multi
    def copy(self, default=None):
        self.ensure_one()

        default = default or {}
        std_default = {
            'code': '/'
        }

        std_default.update(default)
        return super(CrmClaim, self).copy(default=std_default)
