# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .test_rma import TestRma

PROCESSED_STATES = ["received", "refunded", "replaced", "finished"]
AWAITING_ACTION_STATES = ["waiting_return", "waiting_replacement", "confirmed"]


class TestRmaDashboard(TestRma):
    def test_0(self):
        operation_replace = self.env.ref("rma.rma_operation_replace")
        operation_return = self.env.ref("rma.rma_operation_return")
        operation_refund = self.env.ref("rma.rma_operation_refund")
        replace_draft_1 = self._create_rma(
            self.partner, self.product, 1, self.rma_loc, operation=operation_replace
        )
        self._create_rma(
            self.partner, self.product, 1, self.rma_loc, operation=operation_replace
        )  # replace_draft_2
        replace_draft_1.copy({"state": "confirmed"})  # replace_confirmed
        replace_draft_1.copy({"state": "received"})  # replace_received
        replace_draft_1.copy({"state": "waiting_return"})  # replace_waiting_return
        replace_draft_1.copy(  # replace_waiting_replacement
            {"state": "waiting_replacement"}
        )
        return_draft = self._create_rma(
            self.partner, self.product, 1, self.rma_loc, operation=operation_return
        )
        return_draft.copy({"state": "confirmed"})  # return_confirmed
        return_draft.copy({"state": "waiting_return"})  # return_waiting_return
        return_draft.copy({"state": "returned"})  # return_returned
        return_draft.copy({"state": "finished"})  # return_finished
        refund_draft = self._create_rma(
            self.partner, self.product, 1, self.rma_loc, operation=operation_refund
        )
        refund_draft.copy({"state": "finished"})  # refund_refunded

        self.assertEqual(operation_replace.count_rma_draft, 2)
        self.assertEqual(operation_replace.count_rma_awaiting_action, 3)
        self.assertEqual(operation_replace.count_rma_processed, 1)

        self.assertEqual(operation_return.count_rma_draft, 1)
        self.assertEqual(operation_return.count_rma_awaiting_action, 2)
        self.assertEqual(operation_return.count_rma_processed, 1)

        self.assertEqual(operation_refund.count_rma_draft, 1)
        self.assertEqual(operation_refund.count_rma_awaiting_action, 0)
        self.assertEqual(operation_refund.count_rma_processed, 1)

        action = operation_replace.get_action_rma_tree_draft()
        self.assertListEqual(
            ["&", ("operation_id", "=", operation_replace.id), ("state", "=", "draft")],
            action.get("domain"),
        )
        action = operation_replace.get_action_rma_tree_awaiting_action()
        self.assertListEqual(
            [
                "&",
                ("operation_id", "=", operation_replace.id),
                ("state", "in", AWAITING_ACTION_STATES),
            ],
            action.get("domain"),
        )
        action = operation_replace.get_action_rma_tree_processed()
        self.assertListEqual(
            [
                "&",
                ("operation_id", "=", operation_replace.id),
                ("state", "in", PROCESSED_STATES),
            ],
            action.get("domain"),
        )
