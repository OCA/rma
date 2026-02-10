# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form, tagged

from .common import TestRmaBatchReasonCommon


@tagged("-at_install", "post_install")
class TestRmaBatchReason(TestRmaBatchReasonCommon):
    def test_rma_creation_with_batch_reason(self):
        batch = self._create_batch(reason=self.reason)
        rma = self._create_rma(batch=batch)
        self.assertEqual(rma.reason_id, self.reason)

    def test_batch_reason_onchange_propagates_to_draft_rmas(self):
        batch = self._create_batch()
        rma_with_reason = self._create_rma(batch=batch, reason=self.reason)
        rma_without_reason = self._create_rma(batch=batch, reason=None)
        with Form(batch) as batch_form:
            batch_form.reason_id = self.other_reason
            batch_form.save()
            self.assertEqual(rma_with_reason.reason_id, self.reason)
            self.assertEqual(rma_without_reason.reason_id, self.other_reason)

    def test_batch_reason_onchange_does_not_affect_non_draft(self):
        batch = self._create_batch()
        rma_draft = self._create_rma(batch=batch)
        rma_canceled = self._create_rma(batch=batch, reason=self.reason)
        rma_canceled.action_cancel()
        with Form(batch) as batch_form:
            batch_form.reason_id = self.other_reason
            batch_form.save()
            self.assertEqual(rma_draft.reason_id, self.other_reason)
            self.assertEqual(rma_canceled.reason_id, self.reason)

    def test_batch_reason_onchange_all_rmas_already_set(self):
        batch = self._create_batch()
        rma1 = self._create_rma(batch=batch, reason=self.reason)
        rma2 = self._create_rma(batch=batch, reason=self.other_reason)
        with Form(batch) as batch_form:
            batch_form.reason_id = self.env["rma.reason"].create({"name": "New Reason"})
            batch_form.save()
            self.assertEqual(rma1.reason_id, self.reason)
            self.assertEqual(rma2.reason_id, self.other_reason)

    def test_batch_reason_onchange_no_rmas(self):
        batch = self._create_batch()
        with Form(batch) as batch_form:
            batch_form.reason_id = self.reason
            batch_form.save()
            self.assertEqual(batch.reason_id, self.reason)

    def test_batch_reason_onchange_propagates_to_new_rma_after_batch_reason_set(self):
        batch = self._create_batch()
        with Form(batch) as batch_form:
            batch_form.reason_id = self.reason
            batch_form.save()
        rma = self._create_rma(batch=batch)
        self.assertEqual(rma.reason_id, self.reason)

    def test_batch_reason_onchange_on_cancelled_batch(self):
        """reason_id is readonly on cancelled batches but onchange should not fail
        if reason_id is changed programmatically."""
        batch = self._create_batch(reason=self.reason)
        rma = self._create_rma(batch=batch)
        batch.action_cancel()
        batch.reason_id = self.other_reason
        batch._onchange_reason_id()
        self.assertEqual(rma.reason_id, self.reason)
