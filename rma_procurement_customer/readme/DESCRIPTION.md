This module extends the `stock_procurement_customer` module to ensure that the
customer information is automatically propagated to any stock pickings created
as part of an RMA process.

When this module is installed, all stock pickings generated from an RMA —
whether for product reception, delivery, or replacement — will inherit
the customer from the original delivery order.
