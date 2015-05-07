# -*- coding: utf-8 -*-
##############################################################################
#
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

import calendar
import math
from openerp import models, fields, api, SUPERUSER_ID
from openerp.tools.translate import _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
                           DEFAULT_SERVER_DATETIME_FORMAT)
from openerp.exceptions import except_orm


class substate_substate(models.Model):

    """ To precise a state (state=refused; substates= reason 1, 2,...) """
    _name = "substate.substate"
    _description = "substate that precise a given state"

    name = fields.Char('Sub state', required=True)
    substate_descr = fields.Text('Description',
                                 help="To give more "
                                 "information about the sub state")


class claim_line(models.Model):

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
    @api.multi
    def _line_total_amount(self):
        for line in self:
            line.return_value = (line.unit_sale_price *
                                 line.product_returned_quantity)

    def copy_data(self, cr, uid, ids, default=None, context=None):
        if default is None:
            default = {}
        std_default = {
            'move_in_id': False,
            'move_out_id': False,
            'refund_line_id': False,
        }
        std_default.update(default)
        return super(claim_line, self).copy_data(
            cr, uid, ids, default=std_default, context=context)

    @api.model
    def get_warranty_return_partner(self):
        seller = self.env['product.supplierinfo']
        result = seller.get_warranty_return_partner()
        return result

    @api.one
    @api.depends('date_invoice', 'date')
    def _set_priority(self):
        """
        To determine the priority of claim line
        """
        if self.date_invoice:
            days = fields.datetime.strptime(self.date,
                                            '%Y-%m-%d') - \
                fields.datetime.strptime(self.date_invoice,
                                         '%Y-%m-%d')
            if days.days <= 1:
                self.priority = '3_very_high'
            elif days.days <= 7:
                self.priority = '2_high'
            else:
                self.priority = '1_normal'

    company_id = fields.Many2one(
        'res.company', string='Company', readonly=False,
        change_default=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'claim.line'))

    date = fields.Date('Claim Line Date',
                       select=True,
                       default=fields.date.today())

    name = fields.Char('Description', default='none', required=True)

    priority = fields.Selection([('0_not_define', 'Not Define'),
                                ('1_normal', 'Normal'),
                                ('2_high', 'High'),
                                ('3_very_high', 'Very High')],
                                'Priority', default='0_not_define',
                                compute='_set_priority',
                                store=True,
                                readonly=False,
                                help="Priority attention of claim line")

    claim_condition = fields.\
        Selection([('auth_service', 'Authorized Service'),
                   ('supplier', 'Supplier')],
                  help="This field only applies "
                       "for lines with 'RMA-C' type")

    claim_diagnosis = fields.\
        Selection([('damaged', 'Product Damaged'),
                   ('repaired', 'Product Repaired'),
                   ('good', 'Product in good condition'),
                   ('hidden', 'Product with hidden physical damage'),
                   ],
                  string='Claim Diagnosis',
                  help="To describe the line product diagnosis")

    claim_origine = fields.Selection([('none', 'Not specified'),
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
                                      ('other', 'Other')], 'Claim Subject',
                                     required=True,
                                     help="To describe the "
                                     "line product problem")
    claim_descr = fields.Text('Claim description',
                              help="More precise description of the problem")
    product_id = fields.Many2one('product.product',
                                 string='Product',
                                 help="Returned product")
    product_returned_quantity = \
        fields.Float('Quantity', digits=(12, 2),
                     help="Quantity of product returned")
    unit_sale_price = fields.Float('Unit sale price', digits=(12, 2),
                                   help="Unit sale price of the product."
                                   " Auto filled if retrun done "
                                   "by invoice selection. Be careful"
                                   " and check the automatic "
                                   "value as don't take into account"
                                   " previous refunds, invoice "
                                   "discount, can be for 0 if product"
                                   " for free,...")
    return_value = fields.Float(compute='_line_total_amount',
                                string='Total return',
                                help="Quantity returned * Unit sold price",)
    prodlot_id = fields.Many2one('stock.production.lot',
                                 string='Serial/Lot n°',
                                 help="The serial/lot of"
                                      " the returned product")
    applicable_guarantee = fields.Selection([('us', 'Company'),
                                             ('supplier', 'Supplier'),
                                             ('brand', 'Brand manufacturer')],
                                            'Warranty type')
    guarantee_limit = fields.Date('Warranty limit',
                                  readonly=True,
                                  help="The warranty limit is"
                                       " computed as: invoice date + warranty "
                                       "defined on selected product.")
    warning = fields.Char('Warranty',
                          readonly=True,
                          help="If warranty has expired")
    warranty_type = fields.Selection(get_warranty_return_partner,
                                     'Warranty type',
                                     readonly=True,
                                     help="Who is in charge of the warranty "
                                          "return treatment towards "
                                          "the end customer. Company will use "
                                          "the current company "
                                          "delivery or default address  "
                                          "and so on for supplier and brand"
                                          " manufacturer. Does not necessarily"
                                          " mean that the warranty "
                                          "to be applied is the one of the "
                                          "return partner (ie: can be "
                                          "returned to the company and be "
                                          "under the brand warranty")
    warranty_return_partner = \
        fields.Many2one('res.partner', string='Warranty Address',
                        help="Where the customer has to "
                        "send back the product(s)")
    claim_id = fields.Many2one('crm.claim',
                               string='Related claim',
                               ondelete='cascade',
                               help="To link to the case.claim object")
    state = fields.Selection([('draft', 'Draft'), ('refused', 'Refused'),
                              ('confirmed', 'Confirmed, waiting for product'),
                              ('in_to_control', 'Received, to control'),
                              ('in_to_treate', 'Controlled, to treate'),
                              ('treated', 'Treated')], string='State',
                             default='draft')
    substate_id = fields.Many2one('substate.substate', string='Sub state',
                                  help="Select a sub state to precise the"
                                       " standard state. Example 1:"
                                       " state = refused; substate could "
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
                                 # selection=[('customer', 'Customer'),
                                 #            ('supplier', 'Supplier')],
                                 string="Claim Line Type",
                                 store=True,
                                 help="Customer: from customer to company.\n "
                                      "Supplier: from company to supplier.")

    date_invoice = fields.Date(related='invoice_line_id.invoice_id.'
                               'date_invoice',
                               string='Date Invoice',
                               store=True,
                               help="Date of Claim Invoice")

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

    # Method to calculate warranty limit
    @api.one
    @api.model
    def set_warranty_limit(self):
        if not self.date_invoice:
            raise except_orm(
                _('Error'),
                _('Cannot find any date for invoice. '
                  'Must be a validated invoice.'))
        warning = _(self.WARRANT_COMMENT['not_define'])
        date_inv_at_server = datetime.strptime(self.date_invoice,
                                               DEFAULT_SERVER_DATE_FORMAT)
        if self.warranty_type == 'supplier':
            supplier = self.product_id.seller_id
            if not supplier:
                raise except_orm(
                    _('Error'),
                    _('The product has no supplier configured.'))

            psi_obj = self.env['product.supplierinfo']
            domain = [('name', '=', supplier.id),
                      ('product_tmpl_id', '=',
                       self.product_id.product_tmpl_id.id)]
            seller = psi_obj.search(domain)

            warranty_duration = seller.warranty_duration

        else:
            warranty_duration = self.product_id.warranty
        limit = self.warranty_limit(date_inv_at_server, warranty_duration)
        # If waranty period was defined
        if warranty_duration > 0:
            claim_date = datetime.strptime(self.claim_id.date,
                                           DEFAULT_SERVER_DATETIME_FORMAT)
            if limit < claim_date:
                warning = _(self.WARRANT_COMMENT['expired'])
            else:
                warning = _(self.WARRANT_COMMENT['valid'])
        self.write(
            {'guarantee_limit': limit.strftime(DEFAULT_SERVER_DATE_FORMAT),
             'warning': warning},)

    @api.model
    def auto_set_warranty(self):
        """ Set warranty automatically
        if the user has not himself pressed on 'Calculate warranty state'
        button, it sets warranty for him"""
        for line in self:
            if not line.warning:
                line.set_warranty()
        return True

    def get_destination_location(self, cr, uid, product_id,
                                 warehouse_id, context=None):
        """Compute and return the destination location ID to take
        for a return. Always take 'Supplier' one when return type different
        from company."""
        wh_obj = self.pool.get('stock.warehouse')
        wh = wh_obj.browse(cr, uid, warehouse_id, context=context)
        location_dest_id = wh.lot_stock_id.id
        return location_dest_id

    # Method to calculate warranty return address
    @api.one
    @api.model
    def set_warranty_return_address(self):
        """Return the partner to be used as return destination and
        the destination stock location of the line in case of Return.

        We can have various case here:
            - company or other: return to company partner or
              crm_return_address_id if specified
            - supplier: return to the supplier address

        """
        return_address = None
        psi_obj = self.env['product.supplierinfo']
        domain = [('name', '=', self.product_id.seller_id.id),
                  ('product_tmpl_id', '=',
                   self.product_id.product_tmpl_id.id)]
        seller = psi_obj.search(domain)
        if seller:
            return_address_id = seller.warranty_return_address.id
            return_type = seller.warranty_return_partner
        else:
            # when no supplier is configured, returns to the company
            company = self.claim_id.company_id
            return_address = (company.crm_return_address_id or
                              company.partner_id)
            return_address_id = return_address.id
            return_type = 'company'

        location_dest_id = self.get_destination_location(
            self.product_id.id,
            self.claim_id.warehouse_id.id)
        self.write({'warranty_return_partner': return_address_id,
                    'warranty_type': return_type,
                    'location_dest_id': location_dest_id})

    @api.model
    def set_warranty(self):
        """ Calculate warranty limit and address """
        for claim_line_brw in self:
            if not (claim_line_brw.product_id and claim_line.invoice_line_id):
                raise except_orm(
                    _('Error !'),
                    _('Please set product and invoice.'))
            claim_line_brw.set_warranty_return_address()
            claim_line_brw.set_warranty_limit()
        return True


# TODO add the option to split the claim_line in order to manage the same
# product separately
class crm_claim(models.Model):
    _inherit = 'crm.claim'

    def init(self, cr):
        cr.execute("""
            UPDATE "crm_claim"
            SET "number"=id::varchar
            WHERE ("number" is NULL)
               OR ("number" = '/');
        """)

    def _get_sequence_number(self, cr, uid, context=None):
        seq_obj = self.pool.get('ir.sequence')
        res = seq_obj.get(cr, uid, 'crm.claim.rma', context=context) or '/'
        return res

    @api.model
    def _get_default_warehouse(self):
        # TODO must be an smarter method
        user_obj = self.env['res.users']
        user = user_obj.browse(self._uid)
        company_id = user.company_id.id
        wh_obj = self.env['stock.warehouse']
        wh_ids = wh_obj.search([('company_id', '=', company_id)])
        if not wh_ids:
            raise except_orm(
                _('Error!'),
                _('There is no warehouse for the current user\'s company.'))
        return wh_ids[0]

    def name_get(self, cr, uid, ids, context=None):
        res = []
        if isinstance(ids, (int, long)):
            ids = [ids]
        for claim in self.browse(cr, uid, ids, context=context):
            number = claim.number and str(claim.number) or ''
            res.append((claim.id, '[' + number + '] ' + claim.name))
        return res

    def create(self, cr, uid, vals, context=None):
        if ('number' not in vals) or (vals.get('number') == '/'):
            vals['number'] = self._get_sequence_number(cr, uid,
                                                       context=context)
        new_id = super(crm_claim, self).create(cr, uid, vals, context=context)
        return new_id

    def copy_data(self, cr, uid,
                  id, default=None, context=None):  # pylint: disable=W0622
        if default is None:
            default = {}
        std_default = {
            'invoice_ids': False,
            'picking_ids': False,
            'number': self._get_sequence_number(cr, uid, context=context),
        }
        std_default.update(default)
        return super(crm_claim, self).copy_data(
            cr, uid, id, default=std_default, context=context)

    company_id = fields.Many2one(
        change_default=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'crm.claim'))

    number = fields.Char('Number', readonly=True,
                         required=True,
                         select=True,
                         default="/",
                         help="Company internal "
                         "claim unique number")

    @api.model
    def _get_claim_type(self):
        claim_type = self.env['crm.claim.type']
        res = claim_type.search([('active', '=', True)])
        res = [(r.name.lower(), r.name) for r in res]
        return res

    claim_type = \
        fields.Many2one('crm.claim.type',
                        selection=_get_claim_type,
                        string='Claim Type',
                        help="Customer: from customer to company.\n "
                             "Supplier: from company to supplier.")

    stage_id = fields.Many2one('crm.claim.stage',
                               'Stage',
                               track_visibility='onchange',
                               domain="['|', '|', '|',('section_ids', '=', "
                               "section_id), ('case_default', '=', True), "
                               "('claim_type', '=', claim_type)"
                               ",('claim_common', '=', True)]")

    claim_line_ids = fields.One2many('claim.line', 'claim_id',
                                     string='Return lines')
    planned_revenue = fields.Float('Expected revenue')
    planned_cost = fields.Float('Expected cost')
    real_revenue = fields.Float('Real revenue')
    real_cost = fields.Float('Real cost')
    invoice_ids = fields.One2many('account.invoice', 'claim_id', 'Refunds')
    picking_ids = fields.One2many('stock.picking', 'claim_id', 'RMA')
    invoice_id = fields.Many2one('account.invoice', string='Invoice',
                                 help='Related original Cusotmer invoice')
    delivery_address_id = fields.Many2one('res.partner',
                                          string='Partner delivery address',
                                          help="This address will be"
                                          " used to deliver repaired "
                                          "or replacement"
                                          "products.")
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
                                   required=True,
                                   default=_get_default_warehouse)

    # Field "number" is assigned by default with "/"
    # then this constraint ever is broken
    # _sql_constraints = [
    #    ('number_uniq', 'unique(number, company_id)',
    #     'Number/Reference must be unique per Company!'),
    # ]

    def onchange_partner_address_id(self, cr, uid, ids, add, email=False,
                                    context=None):
        res = super(crm_claim, self
                    ).onchange_partner_address_id(cr, uid, ids, add,
                                                  email=email)
        if add:
            if (not res['value']['email_from']
                    or not res['value']['partner_phone']):
                partner_obj = self.pool.get('res.partner')
                address = partner_obj.browse(cr, uid, add, context=context)
                for other_add in address.partner_id.address:
                    if other_add.email and not res['value']['email_from']:
                        res['value']['email_from'] = other_add.email
                    if other_add.phone and not res['value']['partner_phone']:
                        res['value']['partner_phone'] = other_add.phone
        return res

    def onchange_invoice_id(self, cr, uid, ids, invoice_id, warehouse_id,
                            context=None):
        invoice_line_obj = self.pool.get('account.invoice.line')
        invoice_obj = self.pool.get('account.invoice')
        claim_line_obj = self.pool.get('claim.line')
        invoice_line_ids = invoice_line_obj.search(
            cr, uid,
            [('invoice_id', '=', invoice_id)],
            context=context)
        claim_lines = []
        value = {}
        if not warehouse_id:
            warehouse_id = self._get_default_warehouse(cr, uid,
                                                       context=context)
        invoice_lines = invoice_line_obj.browse(cr, uid, invoice_line_ids,
                                                context=context)
        for invoice_line in invoice_lines:
            product_id = invoice_line.product_id\
                and invoice_line.product_id.id or False
            location_dest_id = claim_line_obj.get_destination_location(
                cr, uid, product_id,
                warehouse_id, context=context)
            claim_lines.append({
                'name': invoice_line.name,
                'claim_origine': "none",
                'invoice_line_id': invoice_line.id,
                'product_id': product_id,
                'product_returned_quantity': invoice_line.quantity,
                'unit_sale_price': invoice_line.price_unit,
                'location_dest_id': location_dest_id,
                'state': 'draft',
            })
        value = {'claim_line_ids': claim_lines}
        delivery_address_id = False
        if invoice_id:
            invoice = invoice_obj.browse(cr, uid, invoice_id, context=context)
            delivery_address_id = invoice.partner_id.id
        value['delivery_address_id'] = delivery_address_id

        return {'value': value}

    def message_get_reply_to(self, cr, uid, ids, context=None):
        """ Override to get the reply_to of the parent project. """
        return [claim.section_id.message_get_reply_to()[0]
                if claim.section_id else False
                for claim in self.browse(cr, SUPERUSER_ID, ids,
                                         context=context)]

    def message_get_suggested_recipients(self, cr, uid, ids, context=None):
        recipients = super(crm_claim, self
                           ).message_get_suggested_recipients(cr, uid, ids,
                                                              context=context)
        try:
            for claim in self.browse(cr, uid, ids, context=context):
                if claim.partner_id:
                    self._message_add_suggested_recipient(
                        cr, uid, recipients, claim,
                        partner=claim.partner_id, reason=_('Customer'))
                elif claim.email_from:
                    self._message_add_suggested_recipient(
                        cr, uid, recipients, claim,
                        email=claim.email_from, reason=_('Customer Email'))
        except ValueError:
            # no read access rights -> just ignore suggested recipients
            # because this imply modifying followers
            pass
        return recipients

    @api.onchange('delivery_address_id')
    def _fill_email_and_phone(self):
        """
        When the delivery address is set will add the email and phone data.
        """
        self.email_from = self.delivery_address_id.email
        self.partner_phone = self.delivery_address_id.phone


class crm_claim_type(models.Model):

    _name = 'crm.claim.type'

    name = fields.Char('Name', required=True)
    active = fields.Boolean('Active', default=True)
    description = fields.Text('Decription')


class crm_claim_stage(models.Model):

    _inherit = 'crm.claim.stage'

    @api.model
    def _get_claim_type(self):
        return self.env['crm.claim']._get_claim_type()

    claim_type = \
        fields.Many2one('crm.claim.type',
                        selection=_get_claim_type,
                        string='Claim Type',
                        help="Customer: from customer to company.\n "
                             "Supplier: from company to supplier.")

    claim_common = fields.Boolean('Common to All Claim Types',
                                   help="If you check this field,"
                                   " this stage will be proposed"
                                   " by default on each claim type.")
