# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Eezee-It, MONK Software
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume, Leonardo Donelli
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
import math
import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp import models, fields, api, exceptions
from openerp.tools.misc import (DEFAULT_SERVER_DATE_FORMAT,
                                DEFAULT_SERVER_DATETIME_FORMAT)
from openerp.tools.translate import _


class InvoiceNoDate(Exception):
    """ Raised when a warranty cannot be computed for a claim line
    because the invoice has no date. """


class ProductNoSupplier(Exception):
    """ Raised when a warranty cannot be computed for a claim line
    because the product has no supplier. """


class SubstateSubstate(models.Model):
    """ To precise a state (state=refused; substates= reason 1, 2,...) """
    _name = "substate.substate"
    _description = "substate that precise a given state"

    name = fields.Char(string='Sub state', required=True)
    substate_descr = fields.Text(
        string='Description',
        help="To give more information about the sub state")


class ClaimLine(models.Model):
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

    def get_warranty_return_partner(self):
        return self.env['product.supplierinfo'].get_warranty_return_partner()

    name = fields.Char(string='Description', required=True, default=None)
    claim_origine = fields.Selection(
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
    claim_descr = fields.Text(
        string='Claim description',
        help="More precise description of the problem")
    product_id = fields.Many2one(
        'product.product', string='Product', help="Returned product")
    product_returned_quantity = fields.Float(
        string='Quantity', digits=(12, 2), help="Quantity of product returned")
    unit_sale_price = fields.Float(
        string='Unit sale price', digits=(12, 2),
        help="Unit sale price of the product. Auto filled if retrun done "
             "by invoice selection. Be careful and check the automatic "
             "value as don't take into account previous refunds, invoice "
             "discount, can be for 0 if product for free,...")
    return_value = fields.Float(
        string='Total return', compute='_line_total_amount',
        help="Quantity returned * Unit sold price",)
    prodlot_id = fields.Many2one(
        'stock.production.lot',
        string='Serial/Lot n°', help="The serial/lot of the returned product")
    applicable_guarantee = fields.Selection(
        [('us', 'Company'),
         ('supplier', 'Supplier'),
         ('brand', 'Brand manufacturer')],
        string='Warranty type')
    guarantee_limit = fields.Date(
        string='Warranty limit',
        readonly=True,
        help="The warranty limit is computed as: invoice date + warranty "
             "defined on selected product.")
    warning = fields.Char(
        string='Warranty',
        readonly=True,
        help="If warranty has expired")
    warranty_type = fields.Selection(
        get_warranty_return_partner,
        string='Warranty type',
        readonly=True,
        help="Who is in charge of the warranty return treatment towards "
             "the end customer. Company will use the current company "
             "delivery or default address and so on for supplier and brand"
             " manufacturer. Does not necessarily mean that the warranty "
             "to be applied is the one of the return partner (ie: can be "
             "returned to the company and be under the brand warranty")
    warranty_return_partner = fields.Many2one(
        'res.partner',
        string='Warranty Address',
        help="Where the customer has to send back the product(s)")
    claim_id = fields.Many2one(
        'crm.claim',
        string='Related claim',
        help="To link to the case.claim object")
    state = fields.Selection(
        [('draft', 'Draft'),
         ('refused', 'Refused'),
         ('confirmed', 'Confirmed, waiting for product'),
         ('in_to_control', 'Received, to control'),
         ('in_to_treate', 'Controlled, to treate'),
         ('treated', 'Treated')],
        string='State',
        default="draft")
    substate_id = fields.Many2one(
        'substate.substate',
        string='Sub state',
        help="Select a sub state to precise the standard state. Example 1:"
             " state = refused; substate could be warranty over, not in "
             "warranty, no problem,... . Example 2: state = to treate; "
             "substate could be to refund, to exchange, to repair,...")
    last_state_change = fields.Date(
        string='Last change',
        help="To set the last state / substate change")
    invoice_line_id = fields.Many2one(
        'account.invoice.line',
        string='Invoice Line',
        help='The invoice line related to the returned product')
    refund_line_id = fields.Many2one(
        'account.invoice.line',
        string='Refund Line',
        copy=False,
        help='The refund line related to the returned product')
    move_in_id = fields.Many2one(
        'stock.move',
        string='Move Line from picking in',
        copy=False,
        help='The move line related to the returned product')
    move_out_id = fields.Many2one(
        'stock.move',
        string='Move Line from picking out',
        copy=False,
        help='The move line related to the returned product')
    location_dest_id = fields.Many2one(
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

        warning = 'not_define'
        date_invoice = datetime.strptime(date_invoice,
                                         DEFAULT_SERVER_DATE_FORMAT)

        if isinstance(claim_type, self.env['crm.claim.type'].__class__):
            claim_type = claim_type.id

        if claim_type == self.env.ref('crm_claim_type.'
                                      'crm_claim_type_supplier').id:
            try:
                warranty_duration = product.seller_ids[0].warranty_duration
            except IndexError:
                raise ProductNoSupplier
        else:
            warranty_duration = product.warranty

        limit = self.warranty_limit(date_invoice, warranty_duration)
        if warranty_duration > 0:
            claim_date = datetime.strptime(claim_date,
                                           DEFAULT_SERVER_DATETIME_FORMAT)
            if limit < claim_date:
                warning = 'expired'
            else:
                warning = 'valid'

        return {'guarantee_limit': limit.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'warning': warning}

    def set_warranty_limit(self):
        self.ensure_one()
        claim = self.claim_id
        try:
            values = self._warranty_limit_values(
                claim.invoice_id, claim.claim_type,
                self.product_id, claim.date)
        except InvoiceNoDate:
            raise exceptions.Warning(
                _('Error'), _('Cannot find any date for invoice. '
                              'Must be a validated invoice.'))
        except ProductNoSupplier:
                raise exceptions.Warning(
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

    @api.returns('stock.location')
    def get_destination_location(self, product, warehouse):
        """
        Compute and return the destination location to take
        for a return. Always take 'Supplier' one when return type different
        from company.
        """
        if isinstance(warehouse, int):
            location_dest_id = self.env['stock.warehouse']\
                .browse(warehouse).lot_stock_id
        else:
            location_dest_id = warehouse.lot_stock_id

        if isinstance(product, int):
            product = self.env['product.product']\
                .browse(product)
        try:
            seller = product.seller_ids[0]
            if seller.warranty_return_partner != 'company':
                location_dest_id = seller.name.property_stock_supplier
        finally:
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
        claim_line_model = self.env['claim.line']

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
            warranty = claim_line_model._warranty_limit_values(
                invoice, claim_type, product, claim_date)
        except (InvoiceNoDate, ProductNoSupplier):
            # we don't mind at this point if the warranty can't be
            # computed and we don't want to block the user
            values.update({'guarantee_limit': False, 'warning': False})
        else:
            values.update(warranty)
        warranty_address = claim_line_model._warranty_return_address_values(
            product, company, warehouse)
        values.update(warranty_address)
        self.update(values)

    def _warranty_return_address_values(self, product, company, warehouse):
        """
        Return the partner to be used as return destination and
        the destination stock location of the line in case of return.

        We can have various cases here:
            - company or other: return to company partner or
              crm_return_address_id if specified
            - supplier: return to the supplier address
        """
        if not (product and company and warehouse):
            return {
                'warranty_return_partner': False,
                'warranty_type': False,
                'location_dest_id': False
            }
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
        location_dest = self.get_destination_location(product, warehouse)
        return {
            'warranty_return_partner': return_address_id,
            'warranty_type': return_type,
            'location_dest_id': location_dest.id
        }

    def set_warranty_return_address(self):
        self.ensure_one()
        claim = self.claim_id
        values = self._warranty_return_address_values(
            self.product_id, claim.company_id, claim.warehouse_id)
        self.write(values)
        return True

    @api.one
    def set_warranty(self):
        """ Calculate warranty limit and address """
        if not (self.product_id and self.invoice_line_id):
            raise exceptions.Warning(
                _('Error'), _('Please set product and invoice.'))
        self.set_warranty_limit()
        self.set_warranty_return_address()


# TODO add the option to split the claim_line in order to manage the same
# product separately
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

    @api.one
    def name_get(self):
        return (self.id, u'[{}] {}'.format(self.code or '', self.name))

    claim_line_ids = fields.One2many('claim.line', 'claim_id',
                                     string='Claim lines')
    planned_revenue = fields.Float(string='Expected revenue')
    planned_cost = fields.Float(string='Expected cost')
    real_revenue = fields.Float(string='Real revenue')
    real_cost = fields.Float(string='Real cost')
    invoice_ids = fields.One2many('account.invoice', 'claim_id',
                                  string='Refunds',
                                  copy=False)
    picking_ids = fields.One2many('stock.picking', 'claim_id',
                                  string='RMA',
                                  copy=False)
    invoice_id = fields.Many2one(
        'account.invoice',
        string='Invoice',
        help='Related original Customer invoice')
    delivery_address_id = fields.Many2one(
        'res.partner',
        string='Partner delivery address',
        help="This address will be used to deliver repaired or replacement"
             "products.")
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        default=_get_default_warehouse,
        required=True)

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
                location_dest = claim_line_obj.get_destination_location(
                    invoice_line.product_id, warehouse)
                line = {
                    'name': invoice_line.name,
                    'claim_origine': "none",
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

    @api.multi
    def message_get_reply_to(self):
        """ Override to get the reply_to of the parent project. """
        result = {}
        for claim in self.sudo():
            section = claim.section_id
            if section:
                section_reply_to = section.message_get_reply_to()
                result[claim.id] = section_reply_to[section.id]
            else:
                result[claim.id] = False
        return result

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
