This module extends the delivery_procurement_group_carrier module to ensure
that the carrier is automatically propagated to the RMA procurement group.

The carrier will be assigned to the RMA procurement group based on the strategy
configured for the company (refer to the `rma_delivery` module for more details).
This ensures that the carrier is propagated to the stock moves that share the
rma procurement group, if the stock rule settings are configured to allow it.
