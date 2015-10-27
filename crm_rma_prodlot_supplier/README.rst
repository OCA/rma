.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

============================
CRM RMA Product Lot Supplier
============================

It allows to know the real supplier for a specific product having beforehand its serial/lot number simplifying obtaining it.
For example, when creating/editing a claim for a laptop that it may have two o more suppliers, using this module (taking advantage of lot number) let you know which supplier has provided which specific product related to the claim, or use time frame given by supplier or its address based on stored information about supplier without any aditional steps.

Installation
============

To install this module, just select it from availables modules

Configuration
=============

No configuration is needed

Usage
=====

When a warehouse transfer is made, the supplier field for the product lot is automatically filled.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/145/8.0

For further information, please visit:

* https://www.odoo.com/forum/help-1

Known issues / Roadmap
======================

* The functionalities contained in this module only applies for Invoice Control: Based on generated draft invoices and Based on incoming shipments

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/rma/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/rma/issues/new?body=module:%20crm_rma_prodlot_supplier%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


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
