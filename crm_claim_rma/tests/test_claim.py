# -*- coding: utf-8 -*-
# © 2016 Cyril Gaudin (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase


class TestClaim(TransactionCase):

    def test_create__no_claim_type(self):
        # Just test the case when claim_type is not in values and default value
        # is not yet filled by BaseModel.create as we override this method
        # and our code need claim_type to generate code
        claim = self.env['crm.claim'].create({'name': 'Test claim'})

        self.assertEqual(
            self.env.ref('crm_claim_type.crm_claim_type_customer'),
            claim.claim_type,
        )
        self.assertIsNotNone(claim.code)
        self.assertTrue(claim.code.startswith('RMA-C/'))

    def test_create__with_claim_type(self):
        supplier_type = self.env.ref('crm_claim_type.crm_claim_type_supplier')
        claim = self.env['crm.claim'].create({
            'name': 'Test claim',
            'claim_type': supplier_type.id,
        })

        self.assertEqual(supplier_type, claim.claim_type)
        self.assertIsNotNone(claim.code)
        self.assertTrue(claim.code.startswith('RMA-V/'))

    def test_refund_from_claim(self):
        invoice_ids = self.env.ref('sale.sale_order_4').action_invoice_create()
        invoice = self.env['account.invoice'].browse(invoice_ids[0])
        invoice.invoice_validate()
        invoice_lines = invoice.mapped('invoice_line_ids')
        default_tax = self.env['res.company']._company_default_get('account.tax')
        invoice_lines.write(
            {'invoice_line_tax_ids': [(4, default_tax.id, 0)]}
        )
        claim = self.env['crm.claim'].create({
            'name': 'Test claim',
            'invoice_id': invoice.id
        })
        claim._onchange_invoice()
        claim.claim_line_ids[0].unlink()
        refund_wizard = self.env['account.invoice.refund'].with_context({
            'invoice_ids': [claim.invoice_id.id],
            'claim_line_ids': [(4, line.id, 0) for line in claim.claim_line_ids],
            'description': claim.name,
            'claim_id': claim.id,
        }).create({})
        refund = refund_wizard.compute_refund()
        refund_invoice = self.env['account.invoice'].search(refund['domain'])

        self.assertTrue(refund_invoice)
        self.assertEqual(
            len(refund_invoice.invoice_line_ids),
            len(claim.claim_line_ids)
        )
        self.assertEqual(
            refund_invoice.invoice_line_ids.mapped('invoice_line_tax_ids'),
            claim.claim_line_ids.mapped('invoice_line_id.invoice_line_tax_ids'),
        )
        self.assertEqual(
            refund_invoice.invoice_line_ids.mapped('quantity'),
            claim.claim_line_ids.mapped('product_returned_quantity'),
        )
        self.assertTrue(refund_invoice.tax_line_ids[0].tax_id.refund_account_id)
