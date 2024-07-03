# Copyright 2022 Tecnativa - David Vidal
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Return Merchandise Authorization Management - Link with deliveries",
    "summary": "Allow to choose a default delivery carrier for returns",
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "category": "RMA",
    "website": "https://github.com/OCA/rma",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["chienandalu"],
    "license": "AGPL-3",
    "depends": ["rma", "delivery_procurement_group_carrier"],
    "data": ["views/res_config_settings_views.xml"],
}
