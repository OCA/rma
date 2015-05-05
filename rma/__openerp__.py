# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2010 Vauxoo - http://www.vauxoo.com/
#    All Rights Reserved.
#    info Vauxoo (info@vauxoo.com)
############################################################################
#    Coded by: Yanina Aular <yanina.aular@vauxoo.com>
############################################################################
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
{
    "name": "App RMA",
    "version": "0.1",
    "author": "Vauxoo",
    "category": "RMA",
    "website": "http://vauxoo.com",
    "license": "",
    "depends": [
        "crm_claim_categ_as_name",
        "crm_rma_advance_location",
        "crm_rma_lot_mass_return",
        "crm_rma_stock_location",
        "crm_rma_prodlot_invoice",
        "crm_claim_rma_number",
        "crm_rma_prodlot_supplier",
        "crm_claim_partner_foreign",
        "crm_rma_claim_make_claim",
        "crm_claim_product_supplier",
        "crm_rma_advance_warranty",
        "crm_rma_priority_extended",
        "crm_claim_rma_type",
    ],
    "demo": [],
    "data": [],
    "test": [],
    "js": [],
    "css": [],
    "qweb": [],
    "installable": True,
    "auto_install": False
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
