# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    def _get_next_picking_type_color():
        """ Choose the next available color for the operation types."""
        stock_picking_type = env["stock.picking.type"]
        picking_type = stock_picking_type.search_read(
            [("warehouse_id", "!=", False), ("color", "!=", False)],
            ["color"],
            order="color",
        )
        all_used_colors = [res["color"] for res in picking_type]
        available_colors = [
            color for color in range(0, 12) if color not in all_used_colors
        ]
        return available_colors[0] if available_colors else 0

    def create_rma_locations(warehouse):
        stock_location = env["stock.location"]
        if not warehouse.rma_loc_id:
            rma_location_vals = warehouse._get_rma_location_values()
            warehouse.rma_loc_id = (
                stock_location.with_context(active_test=False)
                .create(rma_location_vals)
                .id
            )

    def create_rma_picking_types(whs):
        ir_sequence_sudo = env["ir.sequence"].sudo()
        stock_picking_type = env["stock.picking.type"]
        color = _get_next_picking_type_color()
        stock_picking = stock_picking_type.search(
            [("sequence", "!=", False)], limit=1, order="sequence desc"
        )
        max_sequence = stock_picking.sequence or 0
        create_data = whs._get_picking_type_create_values(max_sequence)[0]
        sequence_data = whs._get_sequence_values()
        data = {}
        for picking_type, values in create_data.items():
            if (
                picking_type in ["rma_in_type_id", "rma_out_type_id"]
                and not whs[picking_type]
            ):
                picking_sequence = sequence_data[picking_type]
                sequence = ir_sequence_sudo.create(picking_sequence)
                values.update(
                    warehouse_id=whs.id,
                    color=color,
                    sequence_id=sequence.id,
                )
                data[picking_type] = stock_picking_type.create(values).id

        rma_out_type = stock_picking_type.browse(data["rma_out_type_id"])
        rma_out_type.write(
            {"return_picking_type_id": data.get("rma_in_type_id", False)}
        )
        rma_in_type = stock_picking_type.browse(data["rma_in_type_id"])
        rma_in_type.write(
            {"return_picking_type_id": data.get("rma_out_type_id", False)}
        )
        whs.write(data)

    # Create rma locations and picking types
    warehouses = env["stock.warehouse"].search([])
    for warehouse in warehouses:
        create_rma_locations(warehouse)
        create_rma_picking_types(warehouse)
    # Create rma sequence per company
    for company in env["res.company"].search([]):
        company.create_rma_index()
