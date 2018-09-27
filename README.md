[![Build Status](https://travis-ci.org/OCA/rma.svg?branch=12.0)](https://travis-ci.org/OCA/rma)
[![Coverage Status](https://coveralls.io/repos/OCA/rma/badge.png?branch=12.0)](https://coveralls.io/r/OCA/rma?branch=12.0)

RMA (Return Merchandise Authorization) 
=======================================

Management of Return Merchandise Authorization (RMA) in Odoo : product return, warranty control, product exchange, product refund,...

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

***product_warranty***
Extend the warranty details to product/supplier form
* supplier warranty
* return product to company, supplier, brand
* return instructions

***crm_claim_rma***

Management of Return Merchandise Authorization (RMA) in OpenERP.
Upgrade the standard crm_claim module to add :
* product returns (one by one, mass return by invoice)
* warranty control & return address (based on invoice date and product form)
* product picking in / out
* product refund
* product exchange
* access to related customer data (orders, invoices, refunds, picking in/out)



