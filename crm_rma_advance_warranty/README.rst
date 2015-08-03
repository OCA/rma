CRM RMA Advanced Warranty
=========================

- To calculate the warranty using supplier that generates
in the crm_claim_product_supplier using the prodlot of
claim line.

NOTE:

In crm_claim_rma it is calculate take the first seller
in the seller list of product form.

Features
--------

- Modify the set_warranty_return_address method
- Modify the set_warranty_limit method
- Review warranty_limit method and improvement
- Check that the supplier of claim line is in 
  product.supplierinfo list of product.
