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
* product picking in / out
* product refund
* access to related customer data (orders, invoices, refunds, picking
  in/out) from a claim
* use the OpenERP chatter within team like in opportunity (reply to refer to
  the team, not a person)

Using this module makes the logistic flow of return this way:

* Returning product goes into Stock or Supplier location with a incoming
  shipment (depending on the settings of the supplier info in the
  product form)
* You can make a delivery from the RMA to send a new product to the Customer

.. warning:: Currently, the warranty duration used is the one configured on the
             products today, not the one which was configured when the product
             has been sold.

Features
--------

- New field priority in claim line
- Calculate priority of claim line depending of today date and claim date
- Grouping by priority in claim line

Contributors:
-------------

 * Emmanuel Samyn <esamyn@gmail.com>
 * Sébastien Beau <sebastien.beau@akretion.com.br>
 * Benoît Guillot <benoit.guillot@akretion.com.br>
 * Joel Grand-Guillaume <joel.grandguillaume@camptocamp.com>
 * Guewen Baconnier <guewen.baconnier@camptocamp.com>
 * Yannick Vaucher <yannick.vaucher@camptocamp.com>
 * Yanina Aular <yanina.aular@vauxoo.com>



