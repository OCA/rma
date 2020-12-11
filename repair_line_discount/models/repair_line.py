# Copyright 2020, Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RepairOrder(models.Model):
    _inherit = "repair.order"

    def _create_invoices(self, group=False):
        res = super()._create_invoices(group)
        self._add_lines_with_discount()
        return res

    def _add_lines_with_discount(self):
        currency = self.pricelist_id.currency_id
        company = self.env.company
        invoice = self.invoice_id
        invoice.mapped("line_ids").unlink()
        invoice.mapped("invoice_line_ids").unlink()
        invoice_vals = []
        for operation in self.operations:
            account = operation.product_id.product_tmpl_id._get_product_accounts()[
                "income"
            ]
            if not account:
                raise ValidationError(
                    _('No account defined for product "%s".', operation.product_id.name)
                )

            invoice_line_vals = {
                "name": operation.name,
                "account_id": account.id,
                "quantity": operation.product_uom_qty,
                "tax_ids": [(6, 0, operation.tax_id.ids)],
                "product_uom_id": operation.product_uom.id,
                "price_unit": operation.price_unit,
                "product_id": operation.product_id.id,
                "discount": operation.discount,
                "repair_line_ids": [(4, operation.id)],
            }
            if currency == company.currency_id:
                balance = -(operation.product_uom_qty * operation.price_unit)
                invoice_line_vals.update(
                    {
                        "debit": balance > 0.0 and balance or 0.0,
                        "credit": balance < 0.0 and -balance or 0.0,
                    }
                )
            else:
                amount_currency = -(operation.product_uom_qty * operation.price_unit)
                balance = currency._convert(
                    amount_currency, company.currency_id, company, fields.Date.today()
                )
                invoice_line_vals.update(
                    {
                        "amount_currency": amount_currency,
                        "debit": balance > 0.0 and balance or 0.0,
                        "credit": balance < 0.0 and -balance or 0.0,
                        "currency_id": currency.id,
                    }
                )
            invoice_vals.append((0, 0, invoice_line_vals))
        for fee in self.fees_lines:
            invoice_line_vals = {
                "name": fee.name,
                "account_id": account.id,
                "quantity": fee.product_uom_qty,
                "tax_ids": [(6, 0, fee.tax_id.ids)],
                "product_uom_id": fee.product_uom.id,
                "price_unit": fee.price_unit,
                "discount": fee.discount,
                "product_id": fee.product_id.id,
                "repair_fee_ids": [(4, fee.id)],
            }
            if currency == company.currency_id:
                balance = -(fee.product_uom_qty * fee.price_unit)
                invoice_line_vals.update(
                    {
                        "debit": balance > 0.0 and balance or 0.0,
                        "credit": balance < 0.0 and -balance or 0.0,
                    }
                )
            else:
                amount_currency = -(fee.product_uom_qty * fee.price_unit)
                balance = currency._convert(
                    amount_currency, company.currency_id, company, fields.Date.today()
                )
                invoice_line_vals.update(
                    {
                        "amount_currency": amount_currency,
                        "debit": balance > 0.0 and balance or 0.0,
                        "credit": balance < 0.0 and -balance or 0.0,
                        "currency_id": currency.id,
                    }
                )
            invoice_vals.append((0, 0, invoice_line_vals))
        invoice.write({"invoice_line_ids": invoice_vals})


class RepairLine(models.Model):
    _inherit = "repair.line"

    discount = fields.Float()

    @api.depends(
        "price_unit",
        "repair_id",
        "product_uom_qty",
        "product_id",
        "repair_id.invoice_method",
        "discount",
    )
    def _compute_price_subtotal(self):
        for line in self:
            res = super()._compute_price_subtotal()
            line.price_subtotal = line.price_subtotal * (
                1 - (line.discount or 0.0) / 100.0
            )
            return res
