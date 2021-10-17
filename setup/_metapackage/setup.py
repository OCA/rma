import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo9-addons-oca-rma",
    description="Meta package for oca-rma Odoo addons",
    version=version,
    install_requires=[
        'odoo9-addon-crm_claim_rma',
        'odoo9-addon-crm_claim_rma_code',
        'odoo9-addon-crm_rma_location',
        'odoo9-addon-crm_rma_stock_location',
        'odoo9-addon-product_warranty',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 9.0',
    ]
)
