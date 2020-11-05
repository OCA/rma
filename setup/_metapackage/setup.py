import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-rma",
    description="Meta package for oca-rma Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-product_warranty',
        'odoo13-addon-rma',
        'odoo13-addon-rma_sale',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
