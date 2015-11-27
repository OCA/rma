# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Copyright 2014 Camptocamp SA
#    Author: Guewen Baconnier,
#            Osval Reyes
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
from openerp import SUPERUSER_ID


def post_init_hook(cr, registry):
    stock_wh = registry['stock.warehouse']
    for wh_id in stock_wh.browse(cr, SUPERUSER_ID,
                                 stock_wh.search(cr, SUPERUSER_ID, [])):
        vals = stock_wh.create_locations_rma(cr, SUPERUSER_ID, wh_id)
        stock_wh.write(cr, SUPERUSER_ID, wh_id.id, vals)
