# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Copyright 2015 Eezee-It, MONK Software
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume, Leonardo Donelli
#            Osval Reyes <osval@vauxoo.com>
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


from openerp import _
from openerp.exceptions import Warning as UserError


class ProductNoSupplier(UserError):
    """Raised when a warranty cannot be computed for a claim line
    because the product has no supplier.
    """
    def __init__(self):
        super(ProductNoSupplier, self).__init__(
            _("The product has no supplier configured."))


class InvoiceNoDate(UserError):
    """Raised when a warranty cannot be computed for a claim line
    because the invoice has no date.
    """
    def __init__(self):
        super(InvoiceNoDate, self).__init__(
            _("Cannot find any date for invoice. Must be validated."))
