.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Management of Return Merchandise Authorization (RMA)
====================================================

This module aims to improve the Claims by adding a way to manage the
product returns. It allows you to create and manage picking from a
claim. It also introduces a new object: the claim lines to better
handle that problematic. One Claim can have several lines that
concern the return of differents products. It's for every of them
that you'll be able to check the warranty (still running or not).

It mainly contains the following features:

* product returns (one by one, mass return by invoice)
* warranty control & return address (based on invoice date and product form)
* product delivery / return
* product refund
* access to related customer data (orders, invoices, refunds, deliveries,
  returns) from a claim
* use the Odoo chatter within team like in opportunity (reply to refers to
  the team, not a person)

Usage
=====

Using this module makes the logistic flow of return this way:

* Returning product goes into Stock or Supplier location with a incoming
  shipment (depending on the settings of the supplier info in the
  product form)
* You can make a delivery from the RMA to send a new product to the Customer

For further information, please visit:

* https://www.odoo.com/forum/help-1

Known issues / Roadmap
======================

* Currently, the warranty duration used is the one configured on the products
  today, not the one which was configured when the product has been sold.
* If you have removed the default sales team, you need to create an external
  identifier with ID `sales_team.section_sales_department` to a different sales
  team in Settings/Sequences and Identifiers/External Identifiers.

Credits
=======

Contributors
------------

* Emmanuel Samyn <esamyn@gmail.com>
* Sébastien Beau <sebastien.beau@akretion.com.br>
* Benoît Guillot <benoit.guillot@akretion.com.br>
* Joel Grand-Guillaume <joel.grandguillaume@camptocamp.com>
* Guewen Baconnier <guewen.baconnier@camptocamp.com>
* Yannick Vaucher <yannick.vaucher@camptocamp.com>
* Ondřej Kuzník <ondrej.kuznik@credativ.co.uk>

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
