# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from .common import TestRmaSaleStockRestockingFeeInvoicingCommon


class TestRmaMultiStepRoute(TestRmaSaleStockRestockingFeeInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search([], limit=1)
        cls.loc_stock = cls.warehouse.lot_stock_id
        cls.loc_input = cls.warehouse.wh_input_stock_loc_id
        cls.loc_customer = cls.env.ref("stock.stock_location_customers")
        cls.loc_rma_entry = cls.loc_input.copy({"name": "RMA Entry"})
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")
        cls.picking_type_in = cls.env.ref("stock.picking_type_in")
        cls.picking_type_inter = cls.env.ref("stock.picking_type_internal")
        cls.picking_type_rma_in = cls.env["stock.picking.type"].create(
            {
                "name": "RMA reception",
                "code": "incoming",
                "sequence_code": "RMA-IN",
                "default_location_src_id": cls.loc_customer.id,
                "default_location_dest_id": cls.loc_rma_entry.id,
            }
        )

        cls.rma_in_route = cls.env["stock.route"].create(
            {
                "name": "RMA IN in 2 steps",
                "sequence": 1,
                "sale_selectable": True,
                "warehouse_selectable": True,
                "warehouse_ids": [Command.link(cls.warehouse.id)],
                "rule_ids": [
                    Command.create(
                        {
                            "name": "RMA Reception",
                            "action": "pull",
                            "picking_type_id": cls.picking_type_rma_in.id,
                            "location_src_id": cls.loc_customer.id,
                            "location_dest_id": cls.loc_rma_entry.id,
                            "procure_method": "make_to_stock",
                        }
                    ),
                    Command.create(
                        {
                            "name": "RMA Quality Check",
                            "action": "push",
                            "picking_type_id": cls.picking_type_inter.id,
                            "location_src_id": cls.loc_rma_entry.id,
                            "location_dest_id": cls.loc_stock.id,
                            "auto": "manual",
                        }
                    ),
                ],
            }
        )

        cls.warehouse.rma_loc_id = cls.loc_rma_entry
        cls.warehouse.rma_in_type_id = cls.picking_type_rma_in
        cls.warehouse.rma_in_route_id = cls.rma_in_route
        cls.rma_operation_refund = cls.env.ref("rma.rma_operation_refund")

    def test_setup(self):
        """
        Basic unit test to test setup is correct.
        """
        rma = self._create_rma()
        reception_move = rma.reception_move_id
        self.assertEqual(reception_move.location_id, self.loc_customer)
        self.assertEqual(reception_move.location_dest_id, self.loc_rma_entry)
        reception_move.picking_id.button_validate()
        self.assertTrue(reception_move.move_dest_ids)
        qc_move = reception_move.move_dest_ids
        self.assertEqual(qc_move.location_id, self.loc_rma_entry)
        self.assertEqual(qc_move.location_dest_id, self.loc_stock)
        qc_move.picking_id.button_validate()
        self.assertFalse(qc_move.move_dest_ids)

    def test_fixed_restocking_fee_invoice_last_step(self):
        """
        Define fixed restocking fees on the RMA operation, RMA operation with
        a refund operation = "manual after receipt".
        Check that the restocking fee invoice is only created after the
        last move is validated and the refund amount is correct
        """
        self.rma_operation_refund.write(
            {
                "action_create_refund": "manual_after_receipt",
                "restocking_fee_type": "fixed",
                "restocking_fee_amount": 3.2,
            }
        )
        rma = self._create_rma(rma_operation=self.rma_operation_refund)
        self.assertEqual(rma.restocking_fee_type, "fixed")
        self.assertEqual(rma.restocking_fee_amount, 3.2)
        self.assertFalse(rma.restocking_fee_invoice_id)
        # Validate first move
        rma.reception_move_id.picking_id.button_validate()
        self.assertFalse(rma.restocking_fee_invoice_id)
        # Validate last move
        rma.reception_move_id.move_dest_ids.picking_id.button_validate()
        self.assertTrue(rma.restocking_fee_invoice_id)
        self.assertEqual(
            rma.restocking_fee_invoice_id.invoice_line_ids[0].price_unit, 3.2
        )

    def test_percentage_restocking_fee_invoice_last_step(self):
        """
        Define percentage restocking fees on the RMA operation, RMA operation with
        a refund operation = "manual after receipt".
        Check that the restocking fee invoice is only created after the
        last move is validated and the refund amount is correct
        """
        self.rma_operation_refund.write(
            {
                "action_create_refund": "manual_after_receipt",
                "restocking_fee_type": "percent",
                "restocking_fee_amount": 15,
            }
        )
        rma = self._create_rma(rma_operation=self.rma_operation_refund)
        self.assertEqual(rma.restocking_fee_type, "percent")
        self.assertEqual(rma.restocking_fee_amount, 15)
        self.assertFalse(rma.restocking_fee_invoice_id)
        # Validate first move
        rma.reception_move_id.picking_id.button_validate()
        self.assertFalse(rma.restocking_fee_invoice_id)
        # Validate last move
        rma.reception_move_id.move_dest_ids.picking_id.button_validate()
        self.assertTrue(rma.restocking_fee_invoice_id)
        self.assertEqual(
            rma.restocking_fee_invoice_id.invoice_line_ids[0].price_unit,
            self.sale_order.order_line[0].price_unit * 0.15 * rma.product_uom_qty,
        )

    def test_fixed_restocking_fee_on_so_last_step(self):
        """
        Define fixed restocking fees on the RMA operation, RMA operation with
        a refund operation = "update quantities".
        Check that the restocking fee SO line is only created after the
        last move is validated and the amount is correct
        """
        self.rma_operation_refund.write(
            {
                "action_create_refund": "update_quantity",
                "restocking_fee_type": "fixed",
                "restocking_fee_amount": 3.2,
            }
        )
        rma = self._create_rma(rma_operation=self.rma_operation_refund)
        self.assertEqual(rma.restocking_fee_type, "fixed")
        self.assertEqual(rma.restocking_fee_amount, 3.2)
        self.assertEqual(len(self.sale_order.order_line), 1)
        # Validate first move
        rma.reception_move_id.picking_id.button_validate()
        self.assertEqual(len(self.sale_order.order_line), 1)
        # Validate last move
        rma.reception_move_id.move_dest_ids.picking_id.button_validate()
        self.assertEqual(len(self.sale_order.order_line), 2)
        self.assertTrue(self.sale_order.order_line[1].is_restocking_fee)
        self.assertEqual(self.sale_order.order_line[1].price_unit, 3.2)

    def test_percentage_restocking_fee_on_so_last_step(self):
        """
        Define percentage restocking fees on the RMA operation, RMA operation with
        a refund operation = "update quantities".
        Check that the restocking fee SO line is only created after the
        last move is validated and the amount is correct
        """
        self.rma_operation_refund.write(
            {
                "action_create_refund": "update_quantity",
                "restocking_fee_type": "percent",
                "restocking_fee_amount": 15,
            }
        )
        rma = self._create_rma(rma_operation=self.rma_operation_refund)
        self.assertEqual(rma.restocking_fee_type, "percent")
        self.assertEqual(rma.restocking_fee_amount, 15)
        self.assertEqual(len(self.sale_order.order_line), 1)
        # Validate first move
        rma.reception_move_id.picking_id.button_validate()
        self.assertEqual(len(self.sale_order.order_line), 1)
        # Validate last move
        rma.reception_move_id.move_dest_ids.picking_id.button_validate()
        self.assertEqual(len(self.sale_order.order_line), 2)
        self.assertTrue(self.sale_order.order_line[1].is_restocking_fee)
        self.assertEqual(
            self.sale_order.order_line[1].price_unit,
            self.sale_order.order_line[0].price_unit * 0.15 * rma.product_uom_qty,
        )

    def test_restocking_fee_invoice_add_during_process(self):
        """
        Add restocking fees on the RMA in the middle of the process,
        when first reception move is already validated.
        RMA operation refund type is "Manual after receipt".
        Check that the restocking fee invoice is well created (after the
        last move is validated)
        """
        self.rma_operation_refund.write(
            {
                "action_create_refund": "manual_after_receipt",
            }
        )
        rma = self._create_rma(rma_operation=self.rma_operation_refund)
        self.assertFalse(rma.restocking_fee_type)
        self.assertFalse(rma.restocking_fee_invoice_id)
        # Validate first move
        rma.reception_move_id.picking_id.button_validate()
        self.assertFalse(rma.restocking_fee_invoice_id)
        # Add restocking fees and then validate second move
        rma.write(
            {
                "restocking_fee_type": "fixed",
                "restocking_fee_amount": 2,
            }
        )
        rma.reception_move_id.move_dest_ids.picking_id.button_validate()
        self.assertTrue(rma.restocking_fee_invoice_id)

    def test_restocking_fee_on_so_add_during_process(self):
        """
        Add restocking fees on the RMA in the middle of the process,
        when first reception move is already validated.
        RMA operation refund type is "Update quantities".
        Check that the restocking fee SO line is well created (after the
        last move is validated)
        """
        self.rma_operation_refund.write(
            {
                "action_create_refund": "update_quantity",
            }
        )
        rma = self._create_rma(rma_operation=self.rma_operation_refund)
        self.assertFalse(rma.restocking_fee_type)
        self.assertFalse(rma.restocking_fee_invoice_id)
        # Validate first move
        rma.reception_move_id.picking_id.button_validate()
        self.assertEqual(len(self.sale_order.order_line), 1)
        # Add restocking fees and then validate second move
        rma.write(
            {
                "restocking_fee_type": "fixed",
                "restocking_fee_amount": 2,
            }
        )
        rma.reception_move_id.move_dest_ids.picking_id.button_validate()
        self.assertEqual(len(self.sale_order.order_line), 2)
        self.assertTrue(self.sale_order.order_line[1].is_restocking_fee)
