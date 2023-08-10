# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
from odoo.tests import Form, tagged

from ..models.rma_operation import TIMING_ON_CONFIRM
from .test_rma import TestRma


@tagged("post_install", "-at_install")
class TestRmaWorkflow(TestRma):
    @classmethod
    def setUpClass(cls):
        super(TestRmaWorkflow, cls).setUpClass()
        OPER = cls.env["rma.operation"]
        cls.operation = OPER.create(
            {
                "name": "on confirm all",
                "create_return_timing": TIMING_ON_CONFIRM,
                "create_refund_timing": TIMING_ON_CONFIRM,
            }
        )

    def test_rma_on_confirm_all(self):
        origin_delivery = self._create_delivery()
        rma_form = Form(self.env["rma"])
        rma_form.operation_id = self.operation
        rma_form.partner_id = self.partner
        rma_form.picking_id = origin_delivery
        origin_move = origin_delivery.move_lines[0]
        rma_form.move_id = origin_move
        rma = rma_form.save()
        rma.action_confirm()

        self.assertTrue(rma.reception_move_ids)
        self.assertTrue(rma.delivery_move_ids)
        self.assertTrue(rma.refund_id)
