# -*- encoding: utf-8 -*-
# ##############################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://www.vauxoo.com>).
#    All Rights Reserved
# ############ Credits ########################################################
#    Coded by: Yanina Aular <yani@vauxoo.com>
#    Planified by: Yanina Aular <yani@vauxoo.com>
#    Audited by: Moises Lopez <moylop260@vauxoo.com>
#                Nhomar Hernandez <nhomar@vauxoo.com>
# ##############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from openerp import models, api
from openerp.exceptions import except_orm
from openerp.tools.translate import _
from datetime import datetime
# from dateutil.relativedelta import relativedelta
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
                           DEFAULT_SERVER_DATETIME_FORMAT)


class claim_line(models.Model):

    _inherit = 'claim.line'

    # Method to calculate warranty limit
    @api.one
    @api.model
    def set_warranty_limit(self):
        if not self.date_due:
            raise except_orm(
                _('Error'),
                _('Cannot find any date for invoice. '
                  'Must be a validated invoice.'))
        warning = 'not_define'
        date_inv_at_server = datetime.strptime(self.date_due,
                                               DEFAULT_SERVER_DATE_FORMAT)
        if self.warranty_type == 'supplier':
            if self.prodlot_id:
                supplier_rec = self.prodlot_id.supplier_id
                supplier = False
                for seller_rec in self.product_id.seller_ids:
                    if supplier_rec.id == seller_rec.name.id:
                        supplier = supplier_rec
                        break

                if not supplier:
                    raise except_orm(
                        _('Error'),
                        _('The product has no supplier'
                          ' configured for %s.' % supplier_rec.name))

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
        self.write(
            {'guarantee_limit': limit.strftime(DEFAULT_SERVER_DATE_FORMAT),
             'warning': warning},)

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
        supplier = False
        if self.prodlot_id:
            supplier_rec = self.prodlot_id.supplier_id
            supplier = False
            for seller_rec in self.product_id.seller_ids:
                if supplier_rec.id == seller_rec.name.id:
                    supplier = supplier_rec
                    break

        if supplier:
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
            self.product_id.id,
            self.claim_id.warehouse_id.id).id

        self.write({'warranty_return_partner': return_address_id,
                    'warranty_type': return_type,
                    'location_dest_id': location_dest_id})
