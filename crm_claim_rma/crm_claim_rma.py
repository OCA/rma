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
from openerp.osv import fields, orm, osv
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
                           DEFAULT_SERVER_DATETIME_FORMAT)
from openerp.tools.translate import _
from openerp import SUPERUSER_ID


class substate_substate(orm.Model):
    """ To precise a state (state=refused; substates= reason 1, 2,...) """
    _name = "substate.substate"
    _description = "substate that precise a given state"
    _columns = {
        'name': fields.char('Sub state', required=True),
        'substate_descr': fields.text(
            'Description',
            help="To give more information about the sub state"),
    }


class claim_line(orm.Model):
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
    def _line_total_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = (line.unit_sale_price *
                            line.product_returned_quantity)
        return res

    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        std_default = {
            'move_in_id': False,
            'move_out_id': False,
            'refund_line_id': False,
        }
        std_default.update(default)
        return super(claim_line, self).copy_data(
            cr, uid, id, default=std_default, context=context)

    def get_warranty_return_partner(self, cr, uid, context=None):
        seller = self.pool.get('product.supplierinfo')
        result = seller.get_warranty_return_partner(cr, uid, context=context)
        return result

    _columns = {
        'name': fields.char('Description', required=True),
        'claim_origine': fields.selection(
            [('none', 'Not specified'),
             ('legal', 'Legal retractation'),
             ('cancellation', 'Order cancellation'),
             ('damaged', 'Damaged delivered product'),
             ('error', 'Shipping error'),
             ('exchange', 'Exchange request'),
             ('lost', 'Lost during transport'),
             ('other', 'Other')
             ],
            'Claim Subject',
            required=True,
            help="To describe the line product problem"),
        'claim_descr': fields.text(
            'Claim description',
            help="More precise description of the problem"),
        'product_id': fields.many2one(
            'product.product',
            string='Product',
            help="Returned product"),
        'product_returned_quantity': fields.float(
            'Quantity', digits=(12, 2),
            help="Quantity of product returned"),
        'unit_sale_price': fields.float(
            'Unit sale price', digits=(12, 2),
            help="Unit sale price of the product. Auto filled if retrun done "
                 "by invoice selection. Be careful and check the automatic "
                 "value as don't take into account previous refunds, invoice "
                 "discount, can be for 0 if product for free,..."),
        'return_value': fields.function(
            _line_total_amount, string='Total return', type='float',
            help="Quantity returned * Unit sold price",),
        'prodlot_id': fields.many2one(
            'stock.production.lot',
            string='Serial/Lot n°',
            help="The serial/lot of the returned product"),
        'applicable_guarantee': fields.selection(
            [('us', 'Company'),
             ('supplier', 'Supplier'),
             ('brand', 'Brand manufacturer')],
            'Warranty type'),
        'guarantee_limit': fields.date(
            'Warranty limit',
            readonly=True,
            help="The warranty limit is computed as: invoice date + warranty "
                 "defined on selected product."),
        'warning': fields.char(
            'Warranty',
            readonly=True,
            help="If warranty has expired"),
        'warranty_type':  fields.selection(
            get_warranty_return_partner,
            'Warranty type',
            readonly=True,
            help="Who is in charge of the warranty return treatment towards "
                 "the end customer. Company will use the current company "
                 "delivery or default address and so on for supplier and brand"
                 " manufacturer. Does not necessarily mean that the warranty "
                 "to be applied is the one of the return partner (ie: can be "
                 "returned to the company and be under the brand warranty"),
        'warranty_return_partner': fields.many2one(
            'res.partner',
            string='Warranty Address',
            help="Where the customer has to send back the product(s)"),
        'claim_id': fields.many2one(
            'crm.claim', string='Related claim',
            help="To link to the case.claim object"),
        'state': fields.selection(
            [('draft', 'Draft'),
             ('refused', 'Refused'),
             ('confirmed', 'Confirmed, waiting for product'),
             ('in_to_control', 'Received, to control'),
             ('in_to_treate', 'Controlled, to treate'),
             ('treated', 'Treated')],
            string='State'),
        'substate_id': fields.many2one(
            'substate.substate',
            string='Sub state',
            help="Select a sub state to precise the standard state. Example 1:"
                 " state = refused; substate could be warranty over, not in "
                 "warranty, no problem,... . Example 2: state = to treate; "
                 "substate could be to refund, to exchange, to repair,..."),
        'last_state_change': fields.date(
            string='Last change',
            help="To set the last state / substate change"),
        'invoice_line_id': fields.many2one(
            'account.invoice.line',
            string='Invoice Line',
            help='The invoice line related to the returned product'),
        'refund_line_id': fields.many2one(
            'account.invoice.line',
            string='Refund Line',
            help='The refund line related to the returned product'),
        'move_in_id': fields.many2one(
            'stock.move',
            string='Move Line from picking in',
            help='The move line related to the returned product'),
        'move_out_id': fields.many2one(
            'stock.move',
            string='Move Line from picking out',
            help='The move line related to the returned product'),
        'location_dest_id': fields.many2one(
            'stock.location',
            string='Return Stock Location',
            help='The return stock location of the returned product'),
    }

    _defaults = {
        'state': 'draft',
        'name': 'none',
    }

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
    def set_warranty_limit(self, cr, uid, ids, claim_line, context=None):
        date_invoice = claim_line.invoice_line_id.invoice_id.date_invoice
        if not date_invoice:
            raise orm.except_orm(
                _('Error'),
                _('Cannot find any date for invoice. '
                  'Must be a validated invoice.'))
        warning = _(self.WARRANT_COMMENT['not_define'])
        date_inv_at_server = datetime.strptime(date_invoice,
                                               DEFAULT_SERVER_DATE_FORMAT)
        if claim_line.claim_id.claim_type == 'supplier':
            suppliers = claim_line.product_id.seller_ids
            if not suppliers:
                raise orm.except_orm(
                    _('Error'),
                    _('The product has no supplier configured.'))
            supplier = suppliers[0]
            warranty_duration = supplier.warranty_duration
        else:
            warranty_duration = claim_line.product_id.warranty
        limit = self.warranty_limit(date_inv_at_server, warranty_duration)
        # If waranty period was defined
        if warranty_duration > 0:
            claim_date = datetime.strptime(claim_line.claim_id.date,
                                           DEFAULT_SERVER_DATETIME_FORMAT)
            if limit < claim_date:
                warning = _(self.WARRANT_COMMENT['expired'])
            else:
                warning = _(self.WARRANT_COMMENT['valid'])
        self.write(
            cr, uid, ids,
            {'guarantee_limit': limit.strftime(DEFAULT_SERVER_DATE_FORMAT),
             'warning': warning},
            context=context)
        return True

    def auto_set_warranty(self, cr, uid, ids, context):
        """ Set warranty automatically
        if the user has not himself pressed on 'Calculate warranty state'
        button, it sets warranty for him"""
        for line in self.browse(cr, uid, ids, context=context):
            if not line.warning:
                self.set_warranty(cr, uid, [line.id], context=context)
        return True

    def get_destination_location(self, cr, uid, product_id,
                                 warehouse_id, context=None):
        """Compute and return the destination location ID to take
        for a return. Always take 'Supplier' one when return type different
        from company."""
        prod = False
        if product_id:
            prod_obj = self.pool.get('product.product')
            prod = prod_obj.browse(cr, uid, product_id, context=context)
        wh_obj = self.pool.get('stock.warehouse')
        wh = wh_obj.browse(cr, uid, warehouse_id, context=context)
        location_dest_id = wh.lot_stock_id.id
        if prod:
            seller = prod.seller_info_id
            if seller:
                return_type = seller.warranty_return_partner
                if return_type != 'company':
                    location_dest_id = seller.name.property_stock_supplier.id
        return location_dest_id

    # Method to calculate warranty return address
    def set_warranty_return_address(self, cr, uid, ids, claim_line,
                                    context=None):
        """Return the partner to be used as return destination and
        the destination stock location of the line in case of return.

        We can have various case here:
            - company or other: return to company partner or
              crm_return_address_id if specified
            - supplier: return to the supplier address

        """
        return_address = None
        seller = claim_line.product_id.seller_info_id
        if seller:
            return_address_id = seller.warranty_return_address.id
            return_type = seller.warranty_return_partner
        else:
            # when no supplier is configured, returns to the company
            company = claim_line.claim_id.company_id
            return_address = (company.crm_return_address_id or
                              company.partner_id)
            return_address_id = return_address.id
            return_type = 'company'

        location_dest_id = self.get_destination_location(
            cr, uid, claim_line.product_id.id,
            claim_line.claim_id.warehouse_id.id,
            context=context)
        self.write(cr, uid, ids,
                   {'warranty_return_partner': return_address_id,
                    'warranty_type': return_type,
                    'location_dest_id': location_dest_id},
                   context=context)
        return True

    def set_warranty(self, cr, uid, ids, context=None):
        """ Calculate warranty limit and address """
        for claim_line in self.browse(cr, uid, ids, context=context):
            if not (claim_line.product_id and claim_line.invoice_line_id):
                raise orm.except_orm(
                    _('Error !'),
                    _('Please set product and invoice.'))
            self.set_warranty_limit(cr, uid, ids,
                                    claim_line, context=context)
            self.set_warranty_return_address(cr, uid, ids,
                                             claim_line, context=context)
        return True


# TODO add the option to split the claim_line in order to manage the same
# product separately
class crm_claim(orm.Model):
    _inherit = 'crm.claim'

    def init(self, cr):
        cr.execute("""
            UPDATE "crm_claim" SET "number"=id::varchar WHERE ("number" is NULL) 
               OR ("number" = '/');
        """)

    def _get_sequence_number(self, cr, uid, context=None):
        seq_obj = self.pool.get('ir.sequence')
        res = seq_obj.get(cr, uid, 'crm.claim.rma', context=context) or '/'
        return res

    def _get_default_warehouse(self, cr, uid, context=None):
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)
        company_id = user.company_id.id
        wh_obj = self.pool.get('stock.warehouse')
        wh_ids = wh_obj.search(cr, uid,
                               [('company_id', '=', company_id)],
                               context=context)
        if not wh_ids:
            raise orm.except_orm(
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

    def copy_data(self, cr, uid, id, default=None, context=None):
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

    _columns = {
        'number': fields.char(
            'Number', readonly=True,
            states={'draft': [('readonly', False)]},
            required=True,
            select=True,
            help="Company internal claim unique number"),
        'claim_type': fields.selection(
            [('customer', 'Customer'),
             ('supplier', 'Supplier'),
             ('other', 'Other')],
            string='Claim type',
            required=True,
            help="Customer: from customer to company.\n "
                 "Supplier: from company to supplier."),
        'claim_line_ids': fields.one2many(
            'claim.line', 'claim_id',
            string='Return lines'),
        'planned_revenue': fields.float('Expected revenue'),
        'planned_cost': fields.float('Expected cost'),
        'real_revenue': fields.float('Real revenue'),
        'real_cost': fields.float('Real cost'),
        'invoice_ids': fields.one2many(
            'account.invoice', 'claim_id', 'Refunds'),
        'picking_ids': fields.one2many('stock.picking', 'claim_id', 'RMA'),
        'invoice_id': fields.many2one(
            'account.invoice', string='Invoice',
            help='Related original Cusotmer invoice'),
        'delivery_address_id': fields.many2one(
            'res.partner', string='Partner delivery address',
            help="This address will be used to deliver repaired or replacement"
                 "products."),
        'warehouse_id': fields.many2one(
            'stock.warehouse', string='Warehouse',
            required=True),
    }

    _defaults = {
        'number': '/',
        'claim_type': 'customer',
        'warehouse_id': _get_default_warehouse,
    }

    _sql_constraints = [
        ('number_uniq', 'unique(number, company_id)',
         'Number/Reference must be unique per Company!'),
    ]

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
            product_id = invoice_line.product_id and invoice_line.product_id.id or False
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
        except (osv.except_osv, orm.except_orm):
            # no read access rights -> just ignore suggested recipients
            # because this imply modifying followers
            pass
        return recipients
