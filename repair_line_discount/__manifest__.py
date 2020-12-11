# Copyright 2020, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lpgl.html).

{
    "name": "Repair Line Discount",
    "summary": "This module allow add a dicount to models repair line and repair fee",
    "version": "14.0.1.0.0",
    "category": "Reports",
    "website": "https://github.com/OCA/rma",
    "author": "Jarsa Sistemas, S.A. de C.V., Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "depends": ["repair"],
    "data": [
        "views/repair_order_views.xml",
    ],
    "installable": True,
}
