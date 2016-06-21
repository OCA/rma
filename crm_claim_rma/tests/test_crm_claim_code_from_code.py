# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

import openerp.tests.common as common


class TestCrmClaimCode(common.TransactionCase):

    def setUp(self):
        super(TestCrmClaimCode, self).setUp()
        self.crm_claim_model = self.env['crm.claim']
        self.ir_sequence_model = self.env['ir.sequence']
        self.crm_claim = self.env.ref('crm_claim.crm_claim_1')

    def test_old_claim_code_assign(self):
        crm_claims = self.crm_claim_model.search([])
        for crm_claim in crm_claims:
            self.assertNotEqual(crm_claim.code, '/')

    def test_new_claim_code_assign(self):
        claim_type_customer = self.env.ref(
            "crm_claim_rma.crm_claim_type_customer")
        code = self._get_next_code(claim_type_customer.ir_sequence_id)
        crm_claim = self.crm_claim_model.create({
            'name': 'Testing claim code',
            'claim_type': claim_type_customer.id,
        })
        self.assertEqual(crm_claim.code, code)

    def test_copy_claim_code_assign(self):
        code = self._get_next_code(self.crm_claim.claim_type.ir_sequence_id)
        crm_claim_copy = self.crm_claim.copy()
        self.assertNotEqual(crm_claim_copy.code, self.crm_claim.code)
        self.assertRegexpMatches(crm_claim_copy.code, code)

    def _get_next_code(self, crm_sequence):
        d = self.ir_sequence_model._interpolation_dict()
        prefix = self.ir_sequence_model._interpolate(
            crm_sequence.prefix, d)
        suffix = self.ir_sequence_model._interpolate(
            crm_sequence.suffix, d)
        code = (prefix + ('%%0%sd' % crm_sequence.padding %
                          crm_sequence.number_next_actual) + suffix)
        return code
