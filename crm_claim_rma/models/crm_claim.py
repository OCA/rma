# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Eezee-It, MONK Software, Vauxoo
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume, Leonardo Donelli,
#            Osval Reyes, Yanina Aular
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import _, api, exceptions, fields, models

from .invoice_no_date import InvoiceNoDate
from .product_no_supplier import ProductNoSupplier


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    def _get_default_warehouse(self):
        company_id = self.env.user.company_id.id
        wh_obj = self.env['stock.warehouse']
        wh = wh_obj.search([('company_id', '=', company_id)], limit=1)
        if not wh:
            raise exceptions.Warning(
                _('There is no warehouse for the current user\'s company.'))
        return wh

    @api.model
    def _get_company_default(self):
        company_env = self.env['res.company']
        default_company_id = company_env._company_default_get(
            'claim.line')
        return company_env.browse(default_company_id)

    @api.multi
    def name_get(self):
        res = []
        for claim in self:
            code = claim.code and str(claim.code) or ''
            res.append((claim.id, '[' + code + '] ' + claim.name))
        return res

    company_id = fields.Many2one(change_default=True,
                                 default=_get_company_default)

    claim_line_ids = fields.One2many('claim.line', 'claim_id',
                                     string='Return lines')
    planned_revenue = fields.Float('Expected revenue')
    planned_cost = fields.Float('Expected cost')
    real_revenue = fields.Float()
    real_cost = fields.Float()
    invoice_ids = fields.One2many('account.invoice', 'claim_id', 'Refunds',
                                  copy=False)
    picking_ids = fields.One2many('stock.picking', 'claim_id', 'RMA',
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
        claim_type = self.env['crm.claim.type'].search([])
        return claim_type[0] if claim_type else self.env['crm.claim.type']

    claim_type = \
        fields.Many2one(default=_get_claim_type_default,
                        help="Claim classification",
                        required=True)

    @api.onchange('invoice_id', 'warehouse_id', 'claim_type', 'date')
    def _onchange_invoice_warehouse_type_date(self):
        context = self.env.context
        claim_line = self.env['claim.line']
        invoice_lines = self.invoice_id.invoice_line
        if not self.warehouse_id:
            self.warehouse_id = self._get_default_warehouse()
        claim_type = self.claim_type
        claim_date = self.date
        warehouse = self.warehouse_id
        company = self.company_id
        create_lines = context.get('create_lines')

        def warranty_values(invoice, product):
            values = {}
            try:
                warranty = claim_line._warranty_limit_values(
                    invoice, claim_type, product, claim_date)
            except (InvoiceNoDate, ProductNoSupplier):
                # we don't mind at this point if the warranty can't be
                # computed and we don't want to block the user
                values.update({'guarantee_limit': False, 'warning': False})
            else:
                values.update(warranty)

            warranty_address = claim_line._warranty_return_address_values(
                product, company, warehouse)
            values.update(warranty_address)
            return values

        if create_lines:  # happens when the invoice is changed
            claim_lines = []
            for invoice_line in invoice_lines:
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
                line.update(warranty_values(invoice_line.invoice_id,
                                            invoice_line.product_id))
                claim_lines.append((0, 0, line))

            value = self._convert_to_cache(
                {'claim_line_ids': claim_lines}, validate=False)
            self.update(value)

        if self.invoice_id:
            self.delivery_address_id = self.invoice_id.partner_id.id

    @api.model
    def message_get_reply_to(self):
        """ Override to get the reply_to of the parent project. """
        return [claim.section_id.message_get_reply_to()[0]
                if claim.section_id else False
                for claim in self.sudo()]

    @api.multi
    def message_get_suggested_recipients(self):
        recipients = super(CrmClaim, self).message_get_suggested_recipients()
        try:
            for claim in self:
                if claim.partner_id:
                    self._message_add_suggested_recipient(
                        recipients, claim,
                        partner=claim.partner_id, reason=_('Customer'))
                elif claim.email_from:
                    self._message_add_suggested_recipient(
                        recipients, claim,
                        email=claim.email_from, reason=_('Customer Email'))
        except exceptions.AccessError:
            # no read access rights -> just ignore suggested recipients
            # because this imply modifying followers
            pass
        return recipients

    def _get_sequence_number(self, code_id):
        claim_type_code = self.env['crm.claim.type'].\
            browse(code_id).ir_sequence_id.code
        sequence = self.env['ir.sequence']

        return claim_type_code and sequence.get(claim_type_code) or '/'

    @api.model
    def create(self, values):
        values = values or {}
        if 'code' not in values or not values.get('code') \
                or values.get('code') == '/':
            values['code'] = self._get_sequence_number(values['claim_type'])

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
