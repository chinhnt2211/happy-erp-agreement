# Copyright 2025 - Happy ERP
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AgreementSuspensionWizard(models.TransientModel):
    _name = "agreement.suspension.wizard"
    _description = "Agreement Suspension Wizard"

    agreement_id = fields.Many2one(
        "agreement",
        string="Agreement",
        required=True,
        readonly=True,
    )
    date_start = fields.Date(
        string="Suspension start",
        required=True,
    )
    date_end = fields.Date(
        string="Suspension end",
        required=True,
    )
    reason = fields.Text(string="Reason")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get("active_model") == "agreement" and self.env.context.get(
            "active_id"
        ):
            res["agreement_id"] = self.env.context["active_id"]
        return res

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end < rec.date_start:
                raise ValidationError(
                    self.env._("Suspension end date must be >= start date.")
                )

    def action_confirm(self):
        self.ensure_one()
        Suspension = self.env["agreement.suspension"]
        suspension = Suspension.create(
            {
                "agreement_id": self.agreement_id.id,
                "date_start": self.date_start,
                "date_end": self.date_end,
                "reason": self.reason,
                "state": "draft",
            }
        )
        suspension.action_activate()
        return {
            "type": "ir.actions.act_window",
            "res_model": "agreement.suspension",
            "res_id": suspension.id,
            "view_mode": "form",
            "target": "current",
        }
