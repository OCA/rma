# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Eezee-It
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume
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

from openerp.models import Model, api, _
from openerp.fields import (Char, Date, Float, One2many, Many2one, Selection,
                            Text)
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
                           DEFAULT_SERVER_DATETIME_FORMAT)
from openerp.exceptions import except_orm, Warning, ValidationError

import math
import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta


class InvoiceNoDate(Exception):
    """ Raised when a warranty cannot be computed for a claim line
    because the invoice has no date. """


class ProductNoSupplier(Exception):
    """ Raised when a warranty cannot be computed for a claim line
    because the product has no supplier. """


class SubstateSubstate(Model):
    """ To precise a state (state=refused; substates= reason 1, 2,...) """
    _name = "substate.substate"
    _description = "substate that precise a given state"

    name = Char(string='Sub state', required=True)
    substate_descr = Text(string='Description',
                          help="To give more information about the sub state")


class ClaimLine(Model):
    """
    Class to handle a product return line (corresponding to one invoice line)
    """
    _name = "claim.line"
    _description = "List of product to return"

    # Comment written in a claim.line to know about the warranty status
    WARRANT_COMMENT = {
        'valid': "Valid",
        'expired': "Expired",
        'not_define': "Not Defined"}

    # Method to calculate total amount of the line : qty*UP
    @api.one
    def _line_total_amount(self):
        self.return_value = (self.unit_sale_price *
                             self.product_returned_quantity)

    @api.model
    def copy_data(self, default=None):
        if default is None:
            default = {}

        std_default = {
            'move_in_id': False,
            'move_out_id': False,
            'refund_line_id': False,
        }
        std_default.update(default)
        return super(ClaimLine, self).copy_data(default=std_default)

    def get_warranty_return_partner(self):
        seller = self.env['product.supplierinfo']
        result = seller.get_warranty_return_partner()
        return result

    name = Char(string='Description', required=True, default=None)
    claim_origine = Selection(
        [('none', 'Not specified'),
         ('legal', 'Legal retractation'),
         ('cancellation', 'Order cancellation'),
         ('damaged', 'Damaged delivered product'),
         ('error', 'Shipping error'),
         ('exchange', 'Exchange request'),
         ('lost', 'Lost during transport'),
         ('other', 'Other')
         ],
        string='Claim Subject', required=True,
        help="To describe the line product problem")
    claim_descr = Text(
        string='Claim description',
        help="More precise description of the problem")
    product_id = Many2one(
        'product.product', string='Product', help="Returned product")
    product_returned_quantity = Float(
        string='Quantity', digits=(12, 2), help="Quantity of product returned")
    unit_sale_price = Float(
        string='Unit sale price', digits=(12, 2),
        help="Unit sale price of the product. Auto filled if retrun done "
             "by invoice selection. Be careful and check the automatic "
             "value as don't take into account previous refunds, invoice "
             "discount, can be for 0 if product for free,...")
    return_value = Float(
        string='Total return', compute='_line_total_amount',
        help="Quantity returned * Unit sold price",)
    prodlot_id = Many2one(
        'stock.production.lot',
        string='Serial/Lot n°', help="The serial/lot of the returned product")
    applicable_guarantee = Selection(
        [('us', 'Company'),
         ('supplier', 'Supplier'),
         ('brand', 'Brand manufacturer')],
        string='Warranty type')
    guarantee_limit = Date(
        string='Warranty limit',
        readonly=True,
        help="The warranty limit is computed as: invoice date + warranty "
             "defined on selected product.")
    warning = Char(
        string='Warranty',
        readonly=True,
        help="If warranty has expired")
    warranty_type = Selection(
        get_warranty_return_partner,
        string='Warranty type',
        readonly=True,
        help="Who is in charge of the warranty return treatment towards "
             "the end customer. Company will use the current company "
             "delivery or default address and so on for supplier and brand"
             " manufacturer. Does not necessarily mean that the warranty "
             "to be applied is the one of the return partner (ie: can be "
             "returned to the company and be under the brand warranty")
    warranty_return_partner = Many2one(
        'res.partner',
        string='Warranty Address',
        help="Where the customer has to send back the product(s)")
    claim_id = Many2one(
        'crm.claim',
        string='Related claim',
        help="To link to the case.claim object")
    state = Selection(
        [('draft', 'Draft'),
         ('refused', 'Refused'),
         ('confirmed', 'Confirmed, waiting for product'),
         ('in_to_control', 'Received, to control'),
         ('in_to_treate', 'Controlled, to treate'),
         ('treated', 'Treated')],
        string='State',
        default="draft")
    substate_id = Many2one(
        'substate.substate',
        string='Sub state',
        help="Select a sub state to precise the standard state. Example 1:"
             " state = refused; substate could be warranty over, not in "
             "warranty, no problem,... . Example 2: state = to treate; "
             "substate could be to refund, to exchange, to repair,...")
    last_state_change = Date(
        string='Last change',
        help="To set the last state / substate change")
    invoice_line_id = Many2one(
        'account.invoice.line',
        string='Invoice Line',
        help='The invoice line related to the returned product')
    refund_line_id = Many2one(
        'account.invoice.line',
        string='Refund Line',
        help='The refund line related to the returned product')
    move_in_id = Many2one(
        'stock.move',
        string='Move Line from picking in',
        help='The move line related to the returned product')
    move_out_id = Many2one(
        'stock.move',
        string='Move Line from picking out',
        help='The move line related to the returned product')
    location_dest_id = Many2one(
        'stock.location',
        string='Return Stock Location',
        help='The return stock location of the returned product')

    @staticmethod
    def warranty_limit(start, warranty_duration):
        """ Take a duration in float, return the duration in relativedelta

        ``relative_delta(months=...)`` only accepts integers.
        We have to extract the decimal part, and then, extend the delta with
        days.

        """
        decimal_part, months = math.modf(warranty_duration)
        months = int(months)
        # If we have a decimal part, we add the number them as days to
        # the limit.  We need to get the month to know the number of
        # days.
        delta = relativedelta(months=months)
        monthday = start + delta
        __, days_month = calendar.monthrange(monthday.year, monthday.month)
        # ignore the rest of the days (hours) since we expect a date
        days = int(days_month * decimal_part)
        return start + relativedelta(months=months, days=days)

    def _warranty_limit_values(self, invoice, claim_type, product, claim_date):
        if not (invoice and claim_type and product and claim_date):
            return {'guarantee_limit': False, 'warning': False}

        date_invoice = invoice.date_invoice
        if not date_invoice:
            raise InvoiceNoDate

        warning = _(self.WARRANT_COMMENT['not_define'])
        date_invoice = datetime.strptime(date_invoice,
                                         DEFAULT_SERVER_DATE_FORMAT)
        if claim_type == 'supplier':
            suppliers = product.seller_ids
            if not suppliers:
                raise ProductNoSupplier
            supplier = suppliers[0]
            warranty_duration = supplier.warranty_duration
        else:
            warranty_duration = product.warranty

        limit = self.warranty_limit(date_invoice, warranty_duration)
        if warranty_duration > 0:
            claim_date = datetime.strptime(claim_date,
                                           DEFAULT_SERVER_DATETIME_FORMAT)
            if limit < claim_date:
                warning = _(self.WARRANT_COMMENT['expired'])
            else:
                warning = _(self.WARRANT_COMMENT['valid'])

        return {'guarantee_limit': limit.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'warning': warning}

    def set_warranty_limit(self):
        claim = self.claim_id
        invoice = claim.invoice_id
        claim_type = claim.claim_type
        claim_date = claim.date
        product = self.product_id
        try:
            values = self._warranty_limit_values(invoice, claim_type, product,
                                                 claim_date)
        except InvoiceNoDate:
            raise Warning(
                _('Error'), _('Cannot find any date for invoice. '
                              'Must be a validated invoice.'))
        except ProductNoSupplier:
                raise Warning(
                    _('Error'), _('The product has no supplier configured.'))

        self.write(values)
        return True

    @api.multi
    def auto_set_warranty(self):
        """ Set warranty automatically
        if the user has not himself pressed on 'Calculate warranty state'
        button, it sets warranty for him"""
        for line in self:
            if not line.warning:
                line.set_warranty()
        return True

    def get_destination_location(self, product, warehouse):
        """Compute and return the destination location ID to take
        for a return. Always take 'Supplier' one when return type different
        from company."""
        location_dest_id = warehouse.lot_stock_id.id
        if product:
            sellers = product.seller_ids
            if sellers:
                seller = sellers[0]
                return_type = seller.warranty_return_partner
                if return_type != 'company':
                    location_dest_id = seller.name.property_stock_supplier.id
        return location_dest_id

    @api.onchange('product_id', 'invoice_line_id')
    def _onchange_product_invoice_line(self):
        product = self.product_id
        invoice_line = self.invoice_line_id
        context = self.env.context

        claim = context.get('claim_id')
        company_id = context.get('company_id')
        warehouse_id = context.get('warehouse_id')
        claim_type = context.get('claim_type')
        claim_date = context.get('claim_date')

        # claim_exists = not isinstance(claim.id, NewId)
        if not claim and not (company_id and warehouse_id and
                              claim_type and claim_date):
            # if we have a claim_id, we get the info from there,
            # otherwise we get it from the args (on creation typically)
            return False
        if not (product and invoice_line):
            return False

        invoice = invoice_line.invoice_id
        claim_line_obj = self.env['claim.line']

        if claim:
            claim = self.env['crm.claim'].browse(claim)
            company = claim.company_id
            warehouse = claim.warehouse_id
            claim_type = claim.claim_type
            claim_date = claim.date
        else:
            warehouse_obj = self.env['stock.warehouse']
            company_obj = self.env['res.company']
            company = company_obj.browse(company_id)
            warehouse = warehouse_obj.browse(warehouse_id)

        values = {}
        try:
            warranty = claim_line_obj._warranty_limit_values(
                invoice, claim_type, product, claim_date)
        except (InvoiceNoDate, ProductNoSupplier):
            # we don't mind at this point if the warranty can't be
            # computed and we don't want to block the user
            values.update({'guarantee_limit': False, 'warning': False})
        else:
            values.update(warranty)

        warranty_address = claim_line_obj._warranty_return_address_values(
            product, company, warehouse)
        values.update(warranty_address)

        self.update(values)

    def _warranty_return_address_values(self, product, company, warehouse):
        """Return the partner to be used as return destination and
        the destination stock location of the line in case of return.

        We can have various case here:
            - company or other: return to company partner or
              crm_return_address_id if specified
            - supplier: return to the supplier address

        """
        if not (product and company and warehouse):
            return {'warranty_return_partner': False,
                    'warranty_type': False,
                    'location_dest_id': False}
        sellers = product.seller_ids
        if sellers:
            seller = sellers[0]
            return_address_id = seller.warranty_return_address.id
            return_type = seller.warranty_return_partner
        else:
            # when no supplier is configured, returns to the company
            return_address = (company.crm_return_address_id or
                              company.partner_id)
            return_address_id = return_address.id
            return_type = 'company'
        location_dest_id = self.get_destination_location(product, warehouse)
        return {'warranty_return_partner': return_address_id,
                'warranty_type': return_type,
                'location_dest_id': location_dest_id}

    def set_warranty_return_address(self):
        claim = self.claim_id
        product = self.product_id
        company = claim.company_id
        warehouse = claim.warehouse_id
        values = self._warranty_return_address_values(
            product, company, warehouse)
        self.write(values)
        return True

    @api.multi
    def set_warranty(self):
        """ Calculate warranty limit and address """
        for claim_line in self:
            if not (claim_line.product_id and claim_line.invoice_line_id):
                raise Warning(
                    _('Error'), _('Please set product and invoice.'))
            claim_line.set_warranty_limit()
            claim_line.set_warranty_return_address()


# TODO add the option to split the claim_line in order to manage the same
# product separately
class CrmClaim(Model):
    _inherit = 'crm.claim'

    def init(self, cr):
        cr.execute("""
            UPDATE "crm_claim" SET "number"=id::varchar
            WHERE ("number" is NULL)
               OR ("number" = '/');
        """)

    @api.model
    def _get_sequence_number(self):
        seq_obj = self.env['ir.sequence']
        res = seq_obj.get('crm.claim.rma') or '/'
        return res

    def _get_default_warehouse(self):
        company_id = self.env.user.company_id.id
        wh_obj = self.env['stock.warehouse']
        wh = wh_obj.search([('company_id', '=', company_id)], limit=1)
        if not wh:
            raise Warning(
                _('There is no warehouse for the current user\'s company.'))
        return wh

    @api.multi
    def name_get(self):
        res = []
        for claim in self:
            number = claim.number and str(claim.number) or ''
            res.append((claim.id, '[' + number + '] ' + claim.name))
        return res

    @api.model
    def create(self, vals):
        if ('number' not in vals) or (vals.get('number') == '/'):
            vals['number'] = self._get_sequence_number()

        claim = super(CrmClaim, self).create(vals)
        return claim

    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        std_default = {
            'invoice_ids': False,
            'picking_ids': False,
            'number': self._get_sequence_number(cr, uid, context),
        }
        std_default.update(default)
        return super(CrmClaim, self).copy_data(cr, uid, id, std_default,
                                               context=context)

    number = Char(
        string='Number', readonly=True,
        required=True,
        select=True,
        default='/',
        help="Company internal claim unique number")
    claim_type = Selection(
        [('customer', 'Customer'),
         ('supplier', 'Supplier'),
         ('other', 'Other')],
        string='Claim type',
        required=True,
        default='customer',
        help="Customer: from customer to company.\n "
             "Supplier: from company to supplier.")
    claim_line_ids = One2many('claim.line', 'claim_id', string='Return lines')
    planned_revenue = Float(string='Expected revenue')
    planned_cost = Float(string='Expected cost')
    real_revenue = Float(string='Real revenue')
    real_cost = Float(string='Real cost')
    invoice_ids = One2many('account.invoice', 'claim_id', string='Refunds')
    picking_ids = One2many('stock.picking', 'claim_id', string='RMA')
    invoice_id = Many2one(
        'account.invoice',
        string='Invoice',
        help='Related original Customer invoice')
    delivery_address_id = Many2one(
        'res.partner',
        string='Partner delivery address',
        help="This address will be used to deliver repaired or replacement"
             "products.")
    warehouse_id = Many2one(
        'stock.warehouse',
        string='Warehouse',
        default=_get_default_warehouse,
        required=True)

    @api.one
    @api.constrains('number')
    def _check_unq_number(self):
        if self.search([
                ('company_id', '=', self.company_id.id),
                ('number', '=', self.number),
                ('id', '!=', self.id)]):
            raise ValidationError(_('Claim number has to be unique!'))

    @api.onchange('invoice_id', 'warehouse_id', 'claim_type', 'date')
    def _onchange_invoice_warehouse_type_date(self):
        context = self.env.context
        claim_line_obj = self.env['claim.line']
        invoice_lines = self.invoice_id.invoice_line
        claim_lines = []
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
                warranty = claim_line_obj._warranty_limit_values(
                    invoice, claim_type, product, claim_date)
            except (InvoiceNoDate, ProductNoSupplier):
                # we don't mind at this point if the warranty can't be
                # computed and we don't want to block the user
                values.update({'guarantee_limit': False, 'warning': False})
            else:
                values.update(warranty)

            warranty_address = claim_line_obj._warranty_return_address_values(
                product, company, warehouse)
            values.update(warranty_address)
            return values

        if create_lines:  # happens when the invoice is changed
            for invoice_line in invoice_lines:
                location_dest_id = claim_line_obj.get_destination_location(
                    invoice_line.product_id, warehouse)
                line = {
                    'name': invoice_line.name,
                    'claim_origine': "none",
                    'invoice_line_id': invoice_line.id,
                    'product_id': invoice_line.product_id.id,
                    'product_returned_quantity': invoice_line.quantity,
                    'unit_sale_price': invoice_line.price_unit,
                    'location_dest_id': location_dest_id,
                    'state': 'draft',
                }
                line.update(warranty_values(invoice_line.invoice_id,
                                            invoice_line.product_id))
                claim_lines.append([0, 0, line])

        for line in claim_lines:
            value = self._convert_to_cache(
                {'claim_line_ids': line}, validate=False)
            self.update(value)

        if self.invoice_id:
            self.delivery_address_id = self.invoice_id.partner_id.id

    @api.model
    def message_get_reply_to(self):
        """ Override to get the reply_to of the parent project. """
        return [claim.section_id.message_get_reply_to()[0]
                if claim.section_id else False
                for claim in self.sudo()]

    @api.model
    def message_get_suggested_recipients(self):
        recipients = super(CrmClaim, self
                           ).message_get_suggested_recipients()
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
        except except_orm:
            # no read access rights -> just ignore suggested recipients
            # because this imply modifying followers
            pass
        return recipients
