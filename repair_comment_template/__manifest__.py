# Copyright 2021 Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Repair Comments",
    "summary": "Comments texts templates on repair orders documents",
    "version": "14.0.1.0.0",
    "category": "Repair",
    "website": "https://github.com/OCA/rma",
    "author": "Jarsa, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "depends": [
        "base_comment_template",
        "repair",
    ],
    "data": [
        "views/repair_order_view.xml",
        "views/report_repair_order.xml",
    ],
    "installable": True,
}
