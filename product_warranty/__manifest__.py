# Copyright (C) 2009-2011  Akretion, Emmanuel Samyn
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Product Warranty",
    "version": "15.0.1.0.1",
    "category": "Generic Modules/Product",
    "author": "Akretion, Vauxoo, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/rma",
    "license": "AGPL-3",
    "depends": ["sale_management"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_company.xml",
        "views/product_warranty.xml",
        "views/product_template.xml",
    ],
    "demo": ["demo/product_warranty.xml", "demo/res_company.xml"],
    "images": ["images/product_warranty.png"],
    "development_status": "Production/Stable",
    "maintainers": ["osi-scampbell", "max3903"],
}
