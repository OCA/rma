# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume,
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
import calendar
import math
from datetime import datetime

from dateutil.relativedelta import relativedelta

from openerp import _, api, exceptions, fields, models
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
                           DEFAULT_SERVER_DATETIME_FORMAT)

from .invoice_no_date import InvoiceNoDate
from .product_no_supplier import ProductNoSupplier


class ClaimLine(models.Model):

    _name = "claim.line"

    _inherit = 'mail.thread'
    _description = "List of product to return"
    _rec_name = "display_name"

    @api.model
    def _get_company_default(self):
        company_env = self.env['res.company']
        default_company_id = company_env._company_default_get(
            'claim.line')
        return company_env.browse(default_company_id)

    SUBJECT_LIST = [('none', 'Not specified'),
                    ('legal', 'Legal retractation'),
                    ('cancellation', 'Order cancellation'),
                    ('damaged', 'Damaged delivered product'),
                    ('error', 'Shipping error'),
                    ('exchange', 'Exchange request'),
                    ('lost', 'Lost during transport'),
                    ('perfect_conditions',
                     'Perfect Conditions'),
                    ('imperfection', 'Imperfection'),
                    ('physical_damage_client',
                     'Physical Damage by Client'),
                    ('physical_damage_company',
                     'Physical Damage by Company'),
                    ('other', 'Other')]
    WARRANT_COMMENT = [
        ('valid', _("Valid")),
        ('expired', _("Expired")),
        ('not_define', _("Not Defined"))]

    number = fields.Char(
        readonly=True,
        default='/',
        help='Claim Line Identification Number')
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=False,
        change_default=True,
        default=_get_company_default)
    date = fields.Date('Claim Line Date',
                       select=True,
                       default=fields.date.today())
    name = fields.Char('Description', default='none', required=True,
                       help="More precise description of the problem")
    priority = fields.Selection([('0_not_define', 'Not Define'),
                                 ('1_normal', 'Normal'),
                                 ('2_high', 'High'),
                                 ('3_very_high', 'Very High')],
                                'Priority', default='0_not_define',
                                compute='_set_priority',
                                store=True,
                                readonly=False,
                                help="Priority attention of claim line")
    claim_diagnosis = fields.\
        Selection([('damaged', 'Product Damaged'),
                   ('repaired', 'Product Repaired'),
                   ('good', 'Product in good condition'),
                   ('hidden', 'Product with hidden physical damage'),
                   ],
                  help="To describe the line product diagnosis")
    claim_origin = fields.Selection(SUBJECT_LIST, 'Claim Subject',
                                    required=True, help="To describe the "
                                    "line product problem")
    product_id = fields.Many2one('product.product', string='Product',
                                 help="Returned product")
    product_returned_quantity = \
        fields.Float('Quantity', digits=(12, 2),
                     help="Quantity of product returned")
    unit_sale_price = fields.Float(digits=(12, 2),
                                   help="Unit sale price of the product. "
                                   "Auto filled if retrun done "
                                   "by invoice selection. Be careful "
                                   "and check the automatic "
                                   "value as don't take into account "
                                   "previous refunds, invoice "
                                   "discount, can be for 0 if product "
                                   "for free,...")
    return_value = fields.Float(compute='_compute_line_total_amount',
                                string='Total return',
                                help="Quantity returned * Unit sold price",)
    prodlot_id = fields.Many2one('stock.production.lot',
                                 string='Serial/Lot number',
                                 help="The serial/lot of "
                                      "the returned product")
    applicable_guarantee = fields.Selection([('us', 'Company'),
                                             ('supplier', 'Supplier'),
                                             ('brand', 'Brand manufacturer')],
                                            'Warranty type')
    guarantee_limit = fields.Date('Warranty limit', readonly=True,
                                  help="The warranty limit is "
                                       "computed as: invoice date + warranty "
                                       "defined on selected product.")
    warning = fields.Selection(WARRANT_COMMENT,
                               'Warranty', readonly=True,
                               help="If warranty has expired")
    display_name = fields.Char('Name', compute='_get_display_name')

    @api.model
    def get_warranty_return_partner(self):
        return self.env['product.supplierinfo'].get_warranty_return_partner()

    warranty_type = fields.Selection(
        get_warranty_return_partner, readonly=True,
        help="Who is in charge of the warranty return treatment towards "
        "the end customer. Company will use the current company "
        "delivery or default address and so on for supplier and brand "
        "manufacturer. Does not necessarily mean that the warranty "
        "to be applied is the one of the return partner (ie: can be "
        "returned to the company and be under the brand warranty")
    warranty_return_partner = \
        fields.Many2one('res.partner', string='Warranty Address',
                        help="Where the customer has to "
                        "send back the product(s)")
    claim_id = fields.Many2one('crm.claim', string='Related claim',
                               ondelete='cascade',
                               help="To link to the case.claim object")
    state = fields.Selection([('draft', 'Draft'), ('refused', 'Refused'),
                              ('confirmed', 'Confirmed, waiting for product'),
                              ('in_to_control', 'Received, to control'),
                              ('in_to_treate', 'Controlled, to treate'),
                              ('treated', 'Treated')],
                             string='State', default='draft')
    substate_id = fields.Many2one('substate.substate', string='Sub state',
                                  help="Select a sub state to precise the "
                                       "standard state. Example 1: "
                                       "state = refused; substate could "
                                       "be warranty over, not in "
                                       "warranty, no problem,... . "
                                       "Example 2: state = to treate; "
                                       "substate could be to refund, to "
                                       "exchange, to repair,...")
    last_state_change = fields.Date(string='Last change', help="To set the"
                                    "last state / substate change")
    invoice_line_id = fields.Many2one('account.invoice.line',
                                      string='Invoice Line',
                                      help='The invoice line related'
                                      ' to the returned product')
    refund_line_id = fields.Many2one('account.invoice.line',
                                     string='Refund Line',
                                     help='The refund line related'
                                     ' to the returned product')
    move_in_id = fields.Many2one('stock.move',
                                 string='Move Line from picking in',
                                 help='The move line related'
                                 ' to the returned product')
    move_out_id = fields.Many2one('stock.move',
                                  string='Move Line from picking out',
                                  help='The move line related'
                                  ' to the returned product')
    location_dest_id = fields.Many2one('stock.location',
                                       string='Return Stock Location',
                                       help='The return stock location'
                                       ' of the returned product')
    claim_type = fields.Many2one(related='claim_id.claim_type',
                                 string="Claim Line Type",
                                 store=True, help="Claim classification")
    invoice_date = fields.Datetime(related='invoice_line_id.invoice_id.'
                                   'create_date',
                                   help="Date of Claim Invoice")

    # Method to calculate total amount of the line : qty*UP
    @api.multi
    def _compute_line_total_amount(self):
        for line in self:
            line.return_value = (line.unit_sale_price *
                                 line.product_returned_quantity)

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        default = default or {}
        std_default = {
            'move_in_id': False,
            'move_out_id': False,
            'refund_line_id': False,
        }
        std_default.update(default)
        return super(ClaimLine, self).copy(default=std_default)

    @api.depends('invoice_date', 'date')
    def _set_priority(self):
        """
        To determine the priority of claim line
        """
        for line_id in self:
            if line_id.invoice_date:
                days = fields.datetime.strptime(line_id.date, '%Y-%m-%d') - \
                    fields.datetime.strptime(line_id.invoice_date,
                                             DEFAULT_SERVER_DATETIME_FORMAT)
                if days.days <= 1:
                    line_id.priority = '3_very_high'
                elif days.days <= 7:
                    line_id.priority = '2_high'
                else:
                    line_id.priority = '1_normal'

    def _get_subject(self, num):
        if num > 0 and num <= len(self.SUBJECT_LIST):
            return self.SUBJECT_LIST[num - 1][0]
        else:
            return self.SUBJECT_LIST[0][0]

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

        invoice_date = invoice.create_date
        if not invoice_date:
            raise InvoiceNoDate

        warning = 'not_define'
        invoice_date = datetime.strptime(invoice_date,
                                         DEFAULT_SERVER_DATETIME_FORMAT)

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

        limit = self.warranty_limit(invoice_date, warranty_duration)
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
        invoice_id = self.invoice_line_id and self.invoice_line_id.invoice_id \
            or claim.invoice_id
        try:
            values = self._warranty_limit_values(
                invoice_id, claim.claim_type,
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

    @api.model
    def auto_set_warranty(self):
        """ Set warranty automatically
        if the user has not himself pressed on 'Calculate warranty state'
        button, it sets warranty for him"""
        for line in self:
            if not line.warning:
                line.set_warranty()
        return True

    @api.returns('stock.location')
    def get_destination_location(self, product_id, warehouse_id):
        """
        Compute and return the destination location to take
        for a return. Always take 'Supplier' one when return type different
        from company.
        """
        location_dest_id = warehouse_id.lot_stock_id

        if product_id.seller_ids:
            seller = product_id.seller_ids[0]
            if seller.warranty_return_partner != 'company' \
                    and seller.name and \
                    seller.name.property_stock_supplier:
                location_dest_id = seller.name.property_stock_supplier

        return location_dest_id

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

    @api.multi
    def set_warranty(self):
        """
        Calculate warranty limit and address
        """
        for line_id in self:
            if not line_id.product_id:
                raise exceptions.Warning(
                    _('Error'), _('Please set product first'))

            if not line_id.invoice_line_id:
                raise exceptions.Warning(
                    _('Error'), _('Please set invoice first'))

            line_id.set_warranty_limit()
            line_id.set_warranty_return_address()

    @api.model
    def _get_sequence_number(self):
        """
        @return the value of the sequence for the number field in the
        claim.line model.
        """
        return self.env['ir.sequence'].get('claim.line')

    @api.model
    def create(self, vals):
        """
        @return write the identify number once the claim line is create.
        """
        vals = vals or {}

        if ('number' not in vals) or (vals.get('number', False) == '/'):
            vals['number'] = self._get_sequence_number()

        res = super(ClaimLine, self).create(vals)
        return res

    @api.multi
    def _get_display_name(self):
        for line_id in self:
            line_id.display_name = "%s - %s" % (
                line_id.claim_id.code, line_id.name)
