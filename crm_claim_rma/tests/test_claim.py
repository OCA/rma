# -*- coding: utf-8 -*-
# © 2016 Cyril Gaudin (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests import TransactionCase


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
