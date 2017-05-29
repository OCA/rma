# -*- coding: utf-8 -*-
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


class InvoiceNoDate(Exception):
    """ Raised when a warranty cannot be computed for a claim line
    because the invoice has no date.
    """
