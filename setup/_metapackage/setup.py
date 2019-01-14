import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo11-addons-oca-rma",
    description="Meta package for oca-rma Odoo addons",
    version=version,
    install_requires=[
        'odoo11-addon-product_warranty',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
