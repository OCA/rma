.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

====================================================
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

Features
--------

- Sequential code for claims: This module adds a sequential code for claims.

- CRM Claim Types: Includes a way to classify claims adding the concept of type
  and with this, it allows to configure claim stages depending on claim types.
  This module includes Customer, Supplier and Other claim types as default data
  and its own stages relation, and also makes few stages common for different
  claim types.
  It contains a predefined set of claim types. If you want add your own types
  go to Sales > Configurations > Claim > Claim Types.

- New field priority in claim line

- Calculate priority of claim line depending of today date and claim date

- Grouping by priority in claim line

- Stock location: Allow the user to know how much for a product is available 
  'On Hand' and how much is virtually (expected to be) available for 
  RMA locations. Adding for the different product views 
  (Tree, Form and Kanban) information about it. 

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

- RMA Claim Mass Return by Lot: This module adds possibility to return a 
  whole lot of product from an invoice and create a incoming shipment for 
  them based on serial/lot for a product or invoice number.

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

Known issues / Roadmap
======================

* Currently, the warranty duration used is the one configured on the
  products today, not the one which was configured when the product
  has been sold.

* Optimization is possible when searching virtual quantities in the search function

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/rma/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/rma/issues/new?body=module:%20crm_claim_rma%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors:
-------------

* Odoo Community Association (OCA)
* Akretion
* Camptocamp
* Eezee-it
* MONK Software
* Vauxoo
* OdooMRP team
* AvanzOSC
* Serv. Tecnol. Avanzados - Pedro M. Baeza
* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
* Ana Juaristi <anajuarist@avanzosc.es>
* Iker Coranti <ikercoranti@avanzosc.com>
* Oihane Crucelaegui <oihanecrucelaegi@avanzosc.es>
* Alfredo de la Fuente <alfredodelafuente@avanzosc.es>
* Emmanuel Samyn <esamyn@gmail.com>
* Sébastien Beau <sebastien.beau@akretion.com.br>
* Benoît Guillot <benoit.guillot@akretion.com.br>
* Joel Grand-Guillaume <joel.grandguillaume@camptocamp.com>
* Guewen Baconnier <guewen.baconnier@camptocamp.com>
* Yannick Vaucher <yannick.vaucher@camptocamp.com>
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
