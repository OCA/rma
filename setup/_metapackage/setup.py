import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-rma",
    description="Meta package for oca-rma Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-product_warranty',
        'odoo12-addon-rma',
        'odoo12-addon-rma_sale',
        'odoo12-addon-rma_sale_mrp',
        'odoo12-addon-stock_production_lot_warranty',
        'odoo12-addon-website_rma',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 12.0',
    ]
)
