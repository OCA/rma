We compute the kits from the original demanded quantity in the sale order. If
this quantity was to change, we could loose the right components per kit
reference. So this should be very present. Also, v12 has a very poor support
for delivered quantities, that is very improved in v13 with the introduction
of the link to the BoM line in the stock moves. That approach could lead to
errors as well, as the BoM line could change in the future loosing again the
original components per kit reference. Anyway, is to be considered in that
version to use the same rules so they fail for the same reasons.

Some extra features would be nice to have:

* Add actions constraints to disallow actions on single components.
* Show kit components in the portal wizard.
* Allow to make an RMA directly from a kit product.
