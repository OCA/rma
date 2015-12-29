.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

============================
RMA Claim Mass Return by Lot
============================

This module adds possibility to return a whole lot of product from an invoice
and create a incoming shipment for them based on serial/lot for a product or
invoice number.

Installation
============

To install this module, just select it from availables modules

Configuration
=============

No configuration is need for this module

Usage
=====

To use this module, you need to:

* Go into Sales > After-Sale services > Claims

* A button named "Mass return from serial/lot or invoice" will appear in the
  form view when creating or editing an existing claim.

* Enter into the wizard and introduce serial/lot for an invoiced product or
  invoice number and press enter.

* A list of selectable items it will show below or next to the input box
  depending upon is introduced either invoice number or serial/lot number
  respectively. When finish adding, click on Validate button and then Ok
  to exit of wizard and continue editing the claim.


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/145/8.0


For further information, please visit:

* https://www.odoo.com/forum/help-1

Known issues / Roadmap
======================

* No issues are registered

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/rma/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/rma/issues/new?body=module:%20crm_rma_lot_mass_return%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


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
