## Applying a Restocking Fee

1. Create or select a sale order.
2. Deliver the products.
3. Initiate an RMA from the sale order.

The RMA operation determines how the fee will be applied:

### 1. Update Quantity Strategy
If the RMA operation "Refund Action" is "Update Quantities":
- A restocking fee sale order line is automatically added when the last move of the reception chain is validated.
- The fee value depends on the selected fee type.

### 2. Manual Refund Strategy
If the RMA operation uses "Refund Action" is different than "Update Quantities"
- A restocking fee invoice is automatically created when the last move of the reception chain is validated.
