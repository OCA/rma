This module extends the batch RMA process by adding automatic sale order
linking at batch level. It reuses the matching logic provided by the module
`rma_sale_auto_detect`, but allows it to be executed on all RMAs contained
inside an `rma.batch`.

A new batch state **Manual Treatment** is introduced.  
If at least one RMA in the batch fails to auto-match, the batch is moved to
this state, so the user can review and fix the unmatched RMAs manually.