# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Author: Osval Reyes, Yanina Aular
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

from openerp import _, api, exceptions, models
from datetime import datetime
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
                           DEFAULT_SERVER_DATETIME_FORMAT)


class ClaimLine(models.Model):

    _inherit = 'claim.line'

    @api.model
    def set_warranty_limit(self):
        """
        Calculate warranty limit
        """
        if not self.invoice_date:
            raise exceptions.Warning(
                _('Error'),
                _('Cannot find any date for invoice. '
                  'Must be a validated invoice.'))
        warning = 'not_define'
        date_inv_at_server = datetime.strptime(self.invoice_date,
                                               DEFAULT_SERVER_DATETIME_FORMAT)
        if self.warranty_type == 'supplier':
            if self.prodlot_id:
                supplier = self.prodlot_id.supplier_id
                if supplier not in self.product_id.mapped('seller_ids.name'):
                    raise exceptions.Warning(
                        _('Error'),
                        _('The product has no supplier'
                          ' configured for %s.' % supplier.name))

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
                warning = 'expired'
            else:
                warning = 'valid'

        self.write({
            'guarantee_limit': limit.strftime(DEFAULT_SERVER_DATE_FORMAT),
            'warning': warning
        })

    @api.model
    def set_warranty_return_address(self):
        """
        Set the partner to be used as return destination and
        the destination stock location of the line in case of Return.

        We can have various case here:
            - company or other: return to company partner or
              crm_return_address_id if specified
            - supplier: return to the supplier address

        """
        return_address = None
        psi_obj = self.env['product.supplierinfo']
        supplier = self.prodlot_id.supplier_id if self.prodlot_id else False

        if supplier and supplier in self.product_id.mapped('seller_ids.name'):
            domain = [('name', '=', supplier.id),
                      ('product_tmpl_id', '=',
                       self.product_id.product_tmpl_id.id)]
            supplier = psi_obj.search(domain)
            return_address_id = \
                supplier.warranty_return_address.id
            return_type = \
                supplier.warranty_return_partner
        else:
            # when no supplier is configured, returns to the company
            company = self.claim_id.company_id
            return_address = (company.crm_return_address_id or
                              company.partner_id)
            return_address_id = return_address.id
            return_type = 'company'

        location_dest_id = self.get_destination_location(
            self.product_id,
            self.claim_id.warehouse_id).id

        self.write({
            'warranty_return_partner': return_address_id,
            'warranty_type': return_type,
            'location_dest_id': location_dest_id
        })
