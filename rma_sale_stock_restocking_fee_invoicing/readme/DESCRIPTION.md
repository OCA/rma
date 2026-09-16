This module extends the standard RMA flow and the behavior of
`sale_stock_restocking_fee_invoicing` by allowing:

- Fixed or percentage-based restocking fees.
- Restocking fees configurable on the RMA operation or directly on the RMA itself.
- Automatic fee application at last step of RMA receipt.
- Integration with different refund strategies:
  - Update sale order quantity.
  - Manual refund after receipt.
