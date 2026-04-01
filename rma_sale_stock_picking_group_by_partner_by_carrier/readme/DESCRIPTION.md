When ``stock_picking_group_by_partner_by_carrier`` is installed, sale order
pickings are linked via a ``Many2many`` field (``sale_ids``) on the procurement
group instead of the standard ``Many2one`` (``sale_id``).

The ``rma_sale`` module only populates ``sale_id`` when creating the RMA
procurement group. As a result, RMA return pickings become invisible from the
sale order's "Deliveries" button.

This glue module bridges ``sale_id`` → ``sale_ids`` on the procurement group so
that RMA return pickings remain visible from the sale order.
