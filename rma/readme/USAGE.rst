To use this module, you need to:

#. Go to *RMA > Orders* and create a new RMA.
#. Select a partner, an invoice address, select a product
   (or select a picking and a move instead), write a quantity, fill the rest
   of the form and click on 'confirm' button in the status bar.
#. You will see an smart button labeled 'Receipt'. Click on that button to see
   the reception operation form.
#. If everything is right, validate the operation and go back to the RMA to
   see it in a 'received' state.
#. Now you are able to generate a refund, generate a delivery order to return
   to the customer the same product or another product as a replacement, split
   the RMA by extracting a part of the remaining quantity to another RMA,
   preview the RMA in the website. All of these operations can be done by
   clicking on the buttons in the status bar.

   * If you click on 'Refund' button, a refund will be created, and it will be
     accessible via the smart button labeled Refund. The RMA will be set
     automatically to 'Refunded' state when the refund is validated.
   * If you click on 'Replace' or 'Return to customer' button instead,
     a popup wizard will guide you to create a Delivery order to the client
     and this order will be accessible via the smart button labeled Delivery.
     The RMA will be set automatically to 'Replaced' or 'Returned' state when
     the RMA quantity is equal or lower than the quantity in done delivery
     orders linked to it.
#. You can also finish the RMA without further ado. To do so click on the *Finish*
   button. A wizard will ask you for the reason from a selection of preconfigured ones.
   Be sure to configure them in advance on *RMA > Configuration > Finalization Reasons*.
   Once the RMA is finished, it will be set to that state and the reason will be
   registered.

An RMA can also be created from a return of a delivery order:

#. Select a delivery order and click on 'Return' button to create a return.
#. Check "Create RMAs" checkbox in the returning wizard, select the RMA
   stock location and click on 'Return' button.
#. An RMA will be created for each product returned in the previous step.
   Every RMA will be in confirmed state and they will
   be linked to the returning operation generated previously.

There are Optional RMA Teams that can be used for:

  - Organize RMAs in sections.
  - Subscribe users to notifications.
  - Create RMAs from incoming mail to special aliases (See configuration
    section).

To create an RMA Team (RMA Responsible user level required):

  #. Go to *RMA > Configuration > RMA Teams*
  #. Create a new team and assign a name, a responsible and members.
  #. Subscribe users to notifications, that can be of these subtypes:

     - RMA draft. When a new RMA is created.
     - Notes, Debates, Activities. As in standard Odoo.
  #. In the list view, use the cross handle to sort RMA Teams. The top team
     will be the default one if no team is set.
