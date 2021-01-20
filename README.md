[![Runbot Status](https://runbot.odoo-community.org/runbot/badge/flat/145/13.0.svg)](https://runbot.odoo-community.org/runbot/repo/github-com-oca-rma-145)
[![Build Status](https://travis-ci.com/OCA/rma.svg?branch=13.0)](https://travis-ci.com/OCA/rma)
[![codecov](https://codecov.io/gh/OCA/rma/branch/13.0/graph/badge.svg)](https://codecov.io/gh/OCA/rma)
[![Translation Status](https://translation.odoo-community.org/widgets/rma-13-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/rma-13-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# RMA (Return Merchandise Authorization)

Management of Return Merchandise Authorization (RMA) in Odoo : product return, warranty control, product exchange, product refund...

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


<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | summary
--- | --- | ---
[product_warranty](product_warranty/) | 13.0.1.0.0 | Product Warranty
[rma](rma/) | 13.0.1.0.1 | Return Merchandise Authorization (RMA)
[rma_sale](rma_sale/) | 13.0.1.1.0 | Sale Order - Return Merchandise Authorization (RMA)
[website_rma](website_rma/) | 13.0.1.2.0 | Return Merchandise Authorization (RMA)

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to OCA
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----

OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
