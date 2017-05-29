# -*- coding: utf-8 -*-
# © 2015 Vauxoo
# © 2015 Eezee-It, MONK Software
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


class ProductNoSupplier(Exception):
    """ Raised when a warranty cannot be computed for a claim line
    because the product has no supplier.
    """
