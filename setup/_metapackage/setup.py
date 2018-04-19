import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo8-addons-oca-rma",
    description="Meta package for oca-rma Odoo addons",
    version=version,
    install_requires=[
        'odoo8-addon-crm_claim_product_supplier',
        'odoo8-addon-crm_claim_rma',
        'odoo8-addon-crm_claim_rma_code',
        'odoo8-addon-crm_rma_advance_warranty',
        'odoo8-addon-crm_rma_claim_make_claim',
        'odoo8-addon-crm_rma_location',
        'odoo8-addon-crm_rma_lot_mass_return',
        'odoo8-addon-crm_rma_prodlot_invoice',
        'odoo8-addon-crm_rma_prodlot_supplier',
        'odoo8-addon-crm_rma_stock_location',
        'odoo8-addon-product_warranty',
        'odoo8-addon-rma',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
