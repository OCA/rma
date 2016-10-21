# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from .common import ClaimTestsCommon


class TestCrmClaimCode(ClaimTestsCommon):

    def setUp(self):
        super(TestCrmClaimCode, self).setUp()
        self.ir_sequence_model = self.env['ir.sequence']

    def test_old_claim_code_assign(self):
        """Make sure that a code have been taken
        """
        claim_ids = self.env['crm.claim'].search([])
        for claim_id in claim_ids:
            self.assertNotEqual(claim_id.code, '/')

    def test_new_claim_code_assign(self):
        """Test the assigned code is the following next based on sequence
        """
        code = self._get_next_code(self.customer_type.ir_sequence_id)
        claim_id = self.env['crm.claim'].create({
            'name': 'Testing claim code',
            'claim_type': self.customer_type.id,
        })
        self.assertEqual(claim_id.code, code)

    def test_copy_claim_code_assign(self):
        code = self._get_next_code(self.claim_id.claim_type.ir_sequence_id)
        copied_claim_id = self.claim_id.copy()
        self.assertNotEqual(copied_claim_id.code, self.claim_id.code)
        self.assertRegexpMatches(copied_claim_id.code, code)

    def _get_next_code(self, crm_sequence):
        interpolation_dict = self.ir_sequence_model._interpolation_dict()
        prefix = self.ir_sequence_model._interpolate(
            crm_sequence.prefix, interpolation_dict)
        suffix = self.ir_sequence_model._interpolate(
            crm_sequence.suffix, interpolation_dict)
        code = (prefix + ('%%0%sd' % crm_sequence.padding %
                          crm_sequence.number_next_actual) + suffix)
        return code
