import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-rma",
    description="Meta package for oca-rma Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-product_warranty',
        'odoo14-addon-rma',
        'odoo14-addon-rma_sale',
        'odoo14-addon-rma_sale_mrp',
        'odoo14-addon-website_rma',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
