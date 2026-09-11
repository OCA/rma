# Copyright 2026 Studio73 - Eugenio Micó <eugenio@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import Form

from .test_rma import TestRma


class TestRmaAuxiliary(TestRma):
    def test_company_sequences(self):
        companies = self.env["res.company"].create(
            [
                {"name": "RMA test company A"},
                {"name": "RMA test company B"},
            ]
        )
        sequences = self.env["ir.sequence"].search(
            [("code", "=", "rma"), ("company_id", "in", companies.ids)]
        )
        self.assertEqual(sequences.mapped("company_id"), companies)

    def test_partner_and_operation_actions(self):
        empty_action = self.partner.action_view_rma()
        self.assertEqual(
            empty_action["domain"], [("partner_id", "in", self.partner.ids)]
        )

        rma_1 = self._create_rma(self.partner, self.product, 1, self.rma_loc)
        self.assertEqual(self.partner.rma_count, 1)
        self.assertEqual(self.partner.action_view_rma()["res_id"], rma_1.id)

        self._create_rma(self.partner, self.product_2, 1, self.rma_loc)
        self.partner._compute_rma_count()
        self.assertEqual(self.partner.rma_count, 2)
        self.assertIn("domain", self.partner.action_view_rma())
        action = self.operation.get_action_all_rma()
        self.assertEqual(action["domain"], [("operation_id", "=", self.operation.id)])

    def test_picking_rma_actions(self):
        picking = self._create_delivery()
        self.assertEqual(picking.rma_count, 0)
        empty_action = picking.action_view_rma()
        self.assertEqual(empty_action["res_model"], "rma")
        self.assertEqual(empty_action["views"], [(False, "form")])
        self.assertNotIn("domain", empty_action)
        self.assertNotIn("res_id", empty_action)

        rma_1 = self._create_rma(self.partner, self.product, 1, self.rma_loc)
        rma_1.move_id = picking.move_ids[0]
        picking._compute_rma_count()
        self.assertEqual(picking.rma_count, 1)
        singleton_action = picking.action_view_rma()
        self.assertEqual(singleton_action["res_id"], rma_1.id)
        self.assertEqual(singleton_action["views"], [(False, "form")])
        self.assertNotIn("domain", singleton_action)

        rma_2 = self._create_rma(self.partner, picking.move_ids[1].product_id, 1)
        rma_2.move_id = picking.move_ids[1]
        picking._compute_rma_count()
        self.assertEqual(picking.rma_count, 2)
        multiple_action = picking.action_view_rma()
        self.assertEqual(
            multiple_action["domain"], [("id", "in", [rma_1.id, rma_2.id])]
        )
        self.assertEqual(multiple_action["views"], [(False, "list"), (False, "form")])

    def test_team_copy_followers_and_alias_values(self):
        team = self.env["rma.team"].create(
            {
                "name": "Returns team",
                "member_ids": [Command.link(self.user_rma.id)],
            }
        )
        team.message_subscribe(partner_ids=self.partner.ids)
        copied = team.copy()
        self.assertEqual(copied.name, "Returns team (copy)")
        self.assertIn(self.partner, copied.message_partner_ids)
        explicitly_named = team.copy({"name": "Returns team clone"})
        self.assertEqual(explicitly_named.name, "Returns team clone")

        empty_values = self.env["rma.team"]._alias_get_creation_values()
        self.assertEqual(
            empty_values["alias_model_id"], self.env["ir.model"]._get_id("rma")
        )
        values = team._alias_get_creation_values()
        self.assertEqual(values["alias_defaults"]["team_id"], team.id)

    def test_stock_move_helpers_and_unlink(self):
        rma = self._create_rma(self.partner, self.product, 2, self.rma_loc)
        rma.action_confirm()
        reception_move = rma.reception_move_id
        self.assertEqual(reception_move._prepare_move_split_vals(1)["rma_id"], False)
        self.assertNotIn("rma_id", reception_move._prepare_procurement_values())
        reception_move.unlink()
        self.assertEqual(rma.state, "draft")

        received = self._create_confirm_receive(
            self.partner, self.product, 2, self.rma_loc
        )
        received.create_return(False, 1, self.product.uom_id)
        delivery_move = received.delivery_move_ids
        self.assertEqual(
            delivery_move._prepare_move_split_vals(1)["rma_id"], received.id
        )
        self.assertEqual(
            delivery_move._prepare_procurement_values()["rma_id"], received.id
        )
        delivery_move._action_cancel()
        delivery_move.unlink()
        self.assertEqual(received.state, "received")

    def test_warehouse_rename_and_update_values(self):
        warehouse = self.env["stock.warehouse"].create(
            {"name": "RMA rename warehouse", "code": "RRW"}
        )
        warehouse._update_name_and_code("Renamed warehouse", "RNW")
        self.assertTrue(warehouse.rma_in_type_id.sequence_id)
        self.assertTrue(warehouse.rma_out_type_id.sequence_id)

        values = warehouse._get_picking_type_update_values()
        self.assertIn("rma_in_type_id", values)
        hook_values = warehouse.with_context(
            rma_post_init_hook=True
        )._get_picking_type_update_values()
        self.assertEqual(set(hook_values), {"rma_in_type_id", "rma_out_type_id"})

    def test_delivery_wizard_validation_and_onchange(self):
        rma = self._create_confirm_receive(self.partner, self.product, 2, self.rma_loc)
        wizard_model = self.env["rma.delivery.wizard"].with_context(
            active_ids=rma.ids, rma_delivery_type="return"
        )
        with self.assertRaises(ValidationError):
            wizard_model.create({"product_uom_qty": 0})

        wizard = wizard_model.new({"product_id": self.product.id})
        wizard.product_uom = False
        wizard._onchange_product_id()
        self.assertEqual(wizard.product_uom, self.product.uom_id)
        wizard._onchange_product_id()
        self.assertEqual(wizard.product_uom, self.product.uom_id)

        wizard = Form(wizard_model).save()
        wizard.product_uom_qty = 1
        wizard.action_deliver()
        self.assertEqual(rma.state, "waiting_return")

    def test_new_rma_wizard_default_and_open_action(self):
        self.company.rma_new_rma_button_from_rma = True
        rma = self._create_confirm_receive(self.partner, self.product, 1, self.rma_loc)
        rma.create_return(False, 1, self.product.uom_id)
        rma.delivery_move_ids.quantity = 1
        rma.delivery_move_ids.picking_id.button_validate()
        self.assertTrue(rma.can_be_new_rma)

        wizard_model = self.env["rma.rma.wizard"].with_context(active_id=rma.id)
        defaults = wizard_model.default_get(["rma_id", "operation_id"])
        self.assertEqual(defaults["operation_id"], rma.operation_id.id)
        self.assertNotIn(
            "operation_id",
            self.env["rma.rma.wizard"].default_get(["operation_id"]),
        )
        wizard = wizard_model.create({"operation_id": rma.operation_id.id})
        action = wizard.create_and_open_rma()
        self.assertEqual(action["res_model"], "rma")
        self.assertEqual(self.env["rma"].browse(action["res_id"]).state, "confirmed")

    def test_return_wizard_validation_and_dropship_fallback(self):
        picking = self._create_delivery()
        return_wizard = Form(
            self.env["stock.return.picking"].with_context(
                active_id=picking.id,
                active_ids=picking.ids,
                active_model="stock.picking",
            )
        ).save()
        return_wizard.create_rma = False
        return_wizard.product_return_moves.quantity = 1
        action = return_wizard.action_create_returns()
        self.assertEqual(action["res_model"], "stock.picking")

        picking.partner_id = False
        return_wizard.create_rma = True
        return_wizard.rma_operation_id = self.operation
        with self.assertRaises(ValidationError):
            return_wizard.action_create_returns()

        line = return_wizard.product_return_moves[0]
        picking.picking_type_id.warehouse_id = False
        line.rma_operation_id = self.operation
        values = line._prepare_rma_vals()
        self.assertEqual(values["location_id"], self.warehouse.rma_loc_id.id)
