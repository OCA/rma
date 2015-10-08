.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

RMA Claim Advance Location
==========================

This module adds the following location on warehouses :

 * Loss
 * RMA
 * Refurbish

And also various wizards on incoming deliveries that allow you to move your
goods easily in those new locations from a done reception.

Using this module make the logistic flow of return a bit more complex:

 * Returning product goes into RMA location with a incoming shipment
 * From the incoming shipment, forward them to another places (stock, loss,...)

Installation
============

To install this module, you need to select it from available modules

Configuration
=============

This module does not require aditional configuration.

Usage
=====

This module can be used when creating/editing a stock picking, and it allows to return product to stock, send a product to loss location or sending a product to refurbish location, in any of three cases mentioned before it will show a wizard to do that.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/145/8.0

For further information, please visit:

* https://www.odoo.com/forum/help-1

Known issues / Roadmap
======================

* Use with caution, this module is currently not yet completely debugged
  and is waiting his author to be.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/crm_rma_advance_location/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/rma/issues/new?body=module:%20crm_rma_advance_location%0Aversion:%208.0.1.0.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Yanina Aular <yanina.aular@vauxoo.com>
* Osval Reyes <osval@vauxoo.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
