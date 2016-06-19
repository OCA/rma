.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==================
RMA Stock Location
==================

Allow the user to know how much for a product is available 'On Hand' and how much
is virtually (expected to be) available for RMA locations. Adding for the
different product views (Tree, Form and Kanban) information about it.

Both quantities are computed and include its children locations.

It is useful to use it as a quick snapshot for RMA from product perspective.

It also adds the following location on warehouses :

 * Loss
 * Refurbished

Several wizards on incoming deliveries that allow you to move your
goods easily in those new locations from a done reception.

Using this module make the logistic flow of return a bit more complex:

 * Returning product goes into RMA location with a incoming shipment
 * From the incoming shipment, forward them to another places (stock, loss, refurbish)

Installation
============

To install this module, just select it from availables modules.

Configuration
=============

No configuration is needed

Usage
=====

* Go to Sales > After-sale Services and note that 'RMA Quantity On Hand' and
  'RMA Forecasted Quantity' has been included and they'll be shown when at least
  when a product has either on hand or forecasted quantities available.

* In the other hand, it provides three wizards to make stock moves (transfers)
  allowing to do product returns (incoming), send a product to loss or, to a refurbished
  location.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/8.0/145

For further information, please visit:

* https://www.odoo.com/forum/help-1

Known issues / Roadmap
======================

* Optimization is possible when searching virtual quantities in the search function

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/rma/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/rma/issues/new?body=module:%20crm_rma_stock_location%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Guewen Baconnier <guewen.baconnier@camptocamp.com>
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
