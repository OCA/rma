.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
    :alt: License LGPL-3

RMA
===

You use this module to manage RMA (Return Merchandise Authorization) in Odoo

The RMA can be send from the company to the customer or from the supplier to
the company

The RMA user creates the RMA and assign a responsible by selecting the
affected invoice. The available operations are refund, repair and deliver or
replace.
The assigned person checks if the conditions for the RMA are correct and
approve the RMA

The assigned person have to go to the RMA lines from the RMA and operate. THe
available options are creating receipts, delivery orders and refunds.

Once the assigned person considers that the RMA is settled he/she can
set the RMA to Done.


Configuration
=============

To configure this module, you need to:

#. Go to Settings > Users and add the user to the group RMA manager.
#. Go to Inventory > Settings > Return Merchandising Authorization and select
   the option "Display 3 fields on rma: partner, invoice address, delivery
   address" if needed.
#. Go to Inventory > Settings > Configuration > Warehouse management >
   Warehouses and add a default RMA location and RMA picking type for customers
   and suppliers RMA picking type. It's very important to select the type of
   operation supplier if we are moving in the company and customer if we are
   moving out of the company.

Usage
=====

RMA are accessible though Inventory menu. There's four menus, divided by type
. Users can access to the list of RMA or RMA lines.

Create an RMA:
#. Select a partner. Fill the rma lines by selecting an invoice.
#. Request approval and approve.
#. Click on RMA Lines button.
#. Click on more and select an option: "Receive products", "Create Delivery
   Order, Create Refund"
#. Go back to the RMA. Set the RMA to done if not further action is required

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/145/9.0


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/rma/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.


Credits
=======

Contributors
------------

* Jordi Ballester Alomar <jordi.ballester@eficent.com>
* Aaron Henriquez <ahenriquez@eficent.com>


Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
