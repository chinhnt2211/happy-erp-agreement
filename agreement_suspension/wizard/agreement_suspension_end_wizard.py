# Copyright 2025 - Happy ERP
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AgreementSuspensionEndWizard(models.TransientModel):
    _name = "agreement.suspension.end.wizard"
    _description = "End Agreement Suspension Wizard"

    suspension_id = fields.Many2one(
        "agreement.suspension",
        string="Suspension",
        required=True,
        readonly=True,
    )
    date_end_actual = fields.Date(
        string="Actual end date",
        required=True,
        help="Choose the date when the suspension actually ends (between start and \
            configured end). This will be used to extend the agreement end date.",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get(
            "active_model"
        ) == "agreement.suspension" and self.env.context.get("active_id"):
            suspension = self.env["agreement.suspension"].browse(
                self.env.context["active_id"]
            )
            res["suspension_id"] = suspension.id
            # Default: today if within range, else suspension date_end
            today = date.today()
            if suspension.date_start and suspension.date_end:
                if suspension.date_start <= today <= suspension.date_end:
                    res["date_end_actual"] = today
                else:
                    res["date_end_actual"] = suspension.date_end
        return res

    @api.constrains("suspension_id", "date_end_actual")
    def _check_date_in_range(self):
        for rec in self:
            if not rec.suspension_id or not rec.date_end_actual:
                continue
            s = rec.suspension_id
            if s.date_start and rec.date_end_actual < s.date_start:
                raise ValidationError(
                    rec.env._(
                        "Actual end date must be on or after \
                            suspension start (%(start)s).",
                        start=s.date_start,
                    )
                )
            if s.date_end and rec.date_end_actual > s.date_end:
                raise ValidationError(
                    rec.env._(
                        "Actual end date must be on or before \
                            suspension end (%(end)s).",
                        end=s.date_end,
                    )
                )

    def action_confirm(self):
        self.ensure_one()
        self.suspension_id._action_done_with_date(self.date_end_actual)
        return {"type": "ir.actions.act_window_close"}
