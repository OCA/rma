# Copyright 2020 Tecnativa - Ernesto Tejeda
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    # This is a strategic field used to create an rma location
    # and rma operation types in existing warehouses when
    # installing this module.
    rma = fields.Boolean(
        "RMA",
        default=True,
        help="RMA related products can be stored in this warehouse.",
    )
    rma_in_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="RMA In Type",
    )
    rma_out_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="RMA Out Type",
    )
    rma_loc_id = fields.Many2one(
        comodel_name="stock.location",
        string="RMA Location",
    )
    rma_in_route_id = fields.Many2one("stock.route", "RMA in Route")
    rma_out_route_id = fields.Many2one("stock.route", "RMA out Route")
    rma_out_replace_route_id = fields.Many2one("stock.route", "RMA out Replace Route")

    def _get_rma_location_values(self, vals, code=False):
        """this method is intended to be used by 'create' method
        to create a new RMA location to be linked to a new warehouse.
        """
        company_id = vals.get(
            "company_id", self.default_get(["company_id"])["company_id"]
        )
        code = vals.get("code") or code or ""
        code = code.replace(" ", "").upper()
        view_location_id = vals.get("view_location_id")
        view_location = (
            view_location_id
            and self.view_location_id.browse(view_location_id)
            or self.view_location_id
        )
        return {
            "name": view_location.name,
            "active": True,
            "return_location": True,
            "usage": "internal",
            "company_id": company_id,
            "location_id": self.env.ref("rma.stock_location_rma").id,
            "barcode": self._valid_barcode(code + "-RMA", company_id),
        }

    def _get_locations_values(self, vals, code=False):
        res = super()._get_locations_values(vals, code)
        res["rma_loc_id"] = self._get_rma_location_values(vals, code)
        return res

    def _get_sequence_values(self, name=False, code=False):
        values = super()._get_sequence_values(name=name, code=code)
        values.update(
            {
                "rma_in_type_id": {
                    "name": self.name + " " + _("Sequence RMA in"),
                    "prefix": self.code + "/RMA/IN/",
                    "padding": 5,
                    "company_id": self.company_id.id,
                },
                "rma_out_type_id": {
                    "name": self.name + " " + _("Sequence RMA out"),
                    "prefix": self.code + "/RMA/OUT/",
                    "padding": 5,
                    "company_id": self.company_id.id,
                },
            }
        )
        return values

    def _update_name_and_code(self, new_name=False, new_code=False):
        res = super()._update_name_and_code(new_name, new_code)
        for warehouse in self:
            sequence_data = warehouse._get_sequence_values()
            warehouse.rma_in_type_id.sequence_id.write(sequence_data["rma_in_type_id"])
            warehouse.rma_out_type_id.sequence_id.write(
                sequence_data["rma_out_type_id"]
            )
        return res

    def _get_picking_type_create_values(self, max_sequence):
        data, next_sequence = super()._get_picking_type_create_values(max_sequence)
        data.update(
            {
                "rma_in_type_id": {
                    "name": _("RMA Receipts"),
                    "code": "incoming",
                    "use_create_lots": False,
                    "use_existing_lots": True,
                    "default_location_src_id": False,
                    "default_location_dest_id": self.rma_loc_id.id,
                    "sequence": max_sequence + 1,
                    "sequence_code": "RMA/IN",
                    "company_id": self.company_id.id,
                },
                "rma_out_type_id": {
                    "name": _("RMA Delivery Orders"),
                    "code": "outgoing",
                    "use_create_lots": False,
                    "use_existing_lots": True,
                    "default_location_src_id": self.rma_loc_id.id,
                    "default_location_dest_id": False,
                    "sequence": max_sequence + 2,
                    "sequence_code": "RMA/OUT",
                    "company_id": self.company_id.id,
                },
            }
        )
        return data, max_sequence + 3

    def _get_picking_type_update_values(self):
        data = super()._get_picking_type_update_values()
        picking_types = {
            "rma_in_type_id": {"default_location_dest_id": self.rma_loc_id.id},
            "rma_out_type_id": {"default_location_src_id": self.rma_loc_id.id},
        }
        if self.env.context.get("rma_post_init_hook"):
            return picking_types
        data.update(picking_types)
        return data

    def _create_or_update_sequences_and_picking_types(self):
        data = super()._create_or_update_sequences_and_picking_types()
        stock_picking_type = self.env["stock.picking.type"]
        if "out_type_id" in data:
            rma_out_type = stock_picking_type.browse(data["rma_out_type_id"])
            rma_out_type.write(
                {"return_picking_type_id": data.get("rma_in_type_id", False)}
            )
        if "rma_in_type_id" in data:
            rma_in_type = stock_picking_type.browse(data["rma_in_type_id"])
            rma_in_type.write(
                {"return_picking_type_id": data.get("rma_out_type_id", False)}
            )
        return data

    def _get_routes_values(self):
        res = super()._get_routes_values()
        rma_routes = {
            "rma_in_route_id": {
                "routing_key": "rma_in",
                "depends": ["active"],
                "route_update_values": {
                    "name": self._format_routename("RMA In"),
                    "active": self.active,
                },
                "route_create_values": {
                    "warehouse_selectable": True,
                    "company_id": self.company_id.id,
                    "sequence": 100,
                },
                "rules_values": {
                    "active": True,
                },
            },
            "rma_out_route_id": {
                "routing_key": "rma_out",
                "depends": ["active"],
                "route_update_values": {
                    "name": self._format_routename("RMA Out"),
                    "active": self.active,
                },
                "route_create_values": {
                    "warehouse_selectable": True,
                    "company_id": self.company_id.id,
                    "sequence": 110,
                },
                "rules_values": {
                    "active": True,
                },
            },
        }
        if self.env.context.get("rma_post_init_hook"):
            return rma_routes
        res.update(rma_routes)
        return res

    def get_rules_dict(self):
        res = super().get_rules_dict()
        customer_loc, supplier_loc = self._get_partner_locations()
        for warehouse in self:
            res[warehouse.id].update(
                {
                    "rma_in": [
                        self.Routing(
                            customer_loc,
                            warehouse.rma_loc_id,
                            warehouse.rma_in_type_id,
                            "pull",
                        )
                    ],
                    "rma_out": [
                        self.Routing(
                            warehouse.rma_loc_id,
                            customer_loc,
                            warehouse.rma_out_type_id,
                            "pull",
                        )
                    ],
                }
            )
        return res
