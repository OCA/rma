[![Build Status](https://travis-ci.org/OCA/rma.svg?branch=8.0)](https://travis-ci.org/OCA/rma)
[![Coverage Status](https://coveralls.io/repos/OCA/rma/badge.png?branch=8.0)](https://coveralls.io/r/OCA/rma?branch=8.0)

RMA (Return Merchandise Authorization)
======================================

Management of Return Merchandise Authorization (RMA) in Odoo takes care of product returns for customer and supplier, warranty control, product exchange, product refund, product repair. These modules provide tools that complement RMA activities and workflow.

The workflow allowed by this project looks like:

1. Receive an email from customers and automatically creates a Claim
1. Route this claim correctly and affect a responsible and open it
1. Find the invoice concerned by the claim
1. Check the warranty status
1. Choose between various possibilities :
  1. Refuse the Claim (e.g. out of warranty)
  1. Return the customer's goods and send new ones in 2 click
  1. Send the goods to the supplier
  1. Refund the customer


Main modules:

**product_warranty**

Extend the warranty details to product/supplier form
* supplier warranty
* return product to company, supplier, brand
* return instructions

**crm_claim_rma**

Management of Return Merchandise Authorization (RMA) in OpenERP.
Upgrade the standard crm_claim module to add :
* product returns (one by one, mass return by invoice)
* warranty control & return address (based on invoice date and product form)
* product picking in / out
* product refund
* product exchange
* access to related customer data (orders, invoices, refunds, picking in/out)


[//]: # (addons)
Available addons
----------------
addon | version | summary
--- | --- | ---
[crm_claim_product_supplier](crm_claim_product_supplier/) | 8.0.1.0.0 | CRM Claim Product Supplier
[crm_claim_rma](crm_claim_rma/) | 8.0.1.1.1 | RMA Claim (Product Return Management)
[crm_claim_rma_code](crm_claim_rma_code/) | 8.0.1.0.0 | CRM Claim RMA Code
[crm_rma_advance_warranty](crm_rma_advance_warranty/) | 8.0.1.0.0 | CRM RMA Advance Warranty
[crm_rma_claim_make_claim](crm_rma_claim_make_claim/) | 8.0.1.0.0 | CRM RMA Claim Make Claim
[crm_rma_location](crm_rma_location/) | 8.0.1.0.0 | RMA Location
[crm_rma_lot_mass_return](crm_rma_lot_mass_return/) | 8.0.1.0.0 | RMA Claims Mass Return by Lot
[crm_rma_prodlot_invoice](crm_rma_prodlot_invoice/) | 8.0.1.0.0 | CRM Claim Prodlot Invoice
[crm_rma_prodlot_supplier](crm_rma_prodlot_supplier/) | 8.0.1.0.0 | Claim Prodlot Supplier
[crm_rma_stock_location](crm_rma_stock_location/) | 8.0.1.0.0 | RMA Stock Location
[product_warranty](product_warranty/) | 8.0.1.0.0 | Product warranty

Unported addons
---------------
addon | version | summary
--- | --- | ---
[crm_claim_categ_as_name](crm_claim_categ_as_name/) | 1.0 (unported) | crm_claim_categ_as_name
[crm_claim_ext](crm_claim_ext/) | 1.0 (unported) | CRM claim extension
[crm_rma_by_shop](crm_rma_by_shop/) | 1.0 (unported) | RMA Claims by shop

[//]: # (end addons)

Translation status
------------------

[![Transifex Status](https://www.transifex.com/projects/p/OCA-rma-8-0/chart/image_png)](https://www.transifex.com/projects/p/OCA-rma-8-0)
