# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class RmaFinalizationWizard(models.TransientModel):
    _name = "rma.finalization.wizard"
    _description = "RMA Finalization Wizard"

    finalization_id = fields.Many2one(
        comodel_name="rma.finalization", string="Reason", required=True
    )

    def action_finish(self):
        self.ensure_one()
        rma_ids = self.env.context.get("active_ids")
        rma = self.env["rma"].browse(rma_ids)
        rma.write({"finalization_id": self.finalization_id, "state": "finished"})
