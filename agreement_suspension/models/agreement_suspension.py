# Copyright 2025 - Happy ERP
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class AgreementSuspension(models.Model):
    _name = "agreement.suspension"
    _description = "Agreement Suspension"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, id desc"

    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=True,
    )
    agreement_id = fields.Many2one(
        "agreement",
        string="Agreement",
        required=True,
        ondelete="cascade",
        tracking=True,
    )
    date_start = fields.Date(
        string="Suspension start",
        required=True,
        tracking=True,
    )
    date_end = fields.Date(
        string="Suspension end",
        required=True,
        tracking=True,
    )
    actual_end_date = fields.Date(
        string="Actual end date",
        readonly=True,
        help="Date when suspension was actually ended (used to compute extension \
            of agreement end date).",
    )
    days = fields.Integer(
        compute="_compute_days",
        store=True,
        string="Days",
    )
    reason = fields.Text(string="Reason", tracking=True)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("active", "Active"),
            ("done", "Done"),
        ],
        string="State",
        default="draft",
        required=True,
        tracking=True,
    )

    @api.depends("agreement_id", "date_start", "date_end")
    def _compute_name(self):
        for rec in self:
            if rec.agreement_id and rec.date_start and rec.date_end:
                rec.name = (
                    f"{rec.agreement_id.code} ({rec.date_start} → {rec.date_end})"
                )
            else:
                rec.name = "New"

    @api.depends("date_start", "date_end", "actual_end_date")
    def _compute_days(self):
        for rec in self:
            if rec.date_start:
                end = rec.actual_end_date or rec.date_end
                if end:
                    rec.days = (end - rec.date_start).days + 1
                else:
                    rec.days = 0
            else:
                rec.days = 0

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end < rec.date_start:
                raise ValidationError(
                    self.env._("Suspension end date must be >= start date.")
                )

    def action_activate(self):
        """Start suspension: validate and set state to active."""
        for rec in self:
            if rec.state != "draft":
                continue
            rec._check_agreement_dates()
            rec._check_max_suspension_days()
            rec.state = "active"
        return True

    def unlink(self):
        for rec in self:
            if (
                rec.state == "done"
                and rec.actual_end_date
                and rec.agreement_id.end_date
            ):
                # Revert the extension that was applied when suspension was ended
                extra_days = (rec.actual_end_date - rec.date_start).days + 1
                rec.agreement_id.end_date = rec.agreement_id.end_date - timedelta(
                    days=extra_days
                )
        return super().unlink()

    def action_delete(self):
        """Delete selected suspension(s); used by the list view delete button."""
        self.unlink()
        return True

    def action_open_end_wizard(self):
        """Open wizard to choose actual end date and end suspension."""
        self.ensure_one()
        if self.state != "active":
            raise UserError(self.env._("Only active suspensions can be ended."))
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("End suspension"),
            "res_model": "agreement.suspension.end.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_suspension_id": self.id},
        }

    def _action_done_with_date(self, end_date):
        """End suspension with given actual end date; extend agreement end_date."""
        self.ensure_one()
        if self.state != "active":
            raise UserError(self.env._("Only active suspensions can be ended."))
        if not self.agreement_id.end_date:
            raise UserError(self.env._("Agreement has no end date to extend."))
        if end_date < self.date_start or end_date > self.date_end:
            raise ValidationError(
                self.env._(
                    "Actual end date must be between %(start)s and %(end)s.",
                    start=self.date_start,
                    end=self.date_end,
                )
            )
        extra_days = (end_date - self.date_start).days + 1
        self.agreement_id.end_date = self.agreement_id.end_date + timedelta(
            days=extra_days
        )
        self.actual_end_date = end_date
        self.state = "done"
        return True

    def _check_agreement_dates(self):
        """Ensure suspension period is within agreement start/end."""
        self.ensure_one()
        ag = self.agreement_id
        if ag.start_date and self.date_start < ag.start_date:
            raise ValidationError(
                self.env._(
                    "Suspension start must be on or after agreement \
                        start date (%(start)s).",
                    start=ag.start_date,
                )
            )
        if ag.end_date and self.date_end > ag.end_date:
            raise ValidationError(
                self.env._(
                    "Suspension end must be on or before agreement \
                        end date (%(end)s).",
                    end=ag.end_date,
                )
            )

    @api.model
    def _cron_auto_end_suspensions(self):
        """Auto-end active suspensions whose configured end date has passed."""
        today = fields.Date.context_today(self)
        active_past = self.search([("state", "=", "active"), ("date_end", "<", today)])
        for suspension in active_past:
            try:
                suspension._action_done_with_date(suspension.date_end)
            except (UserError, ValidationError):
                continue

    def _check_max_suspension_days(self):
        """Ensure total suspension days do not exceed agreement max."""
        self.ensure_one()
        ag = self.agreement_id
        if not ag.max_suspension_days or ag.max_suspension_days <= 0:
            return
        if ag.total_suspension_days_used > ag.max_suspension_days:
            raise ValidationError(
                self.env._(
                    "Total suspension days (%(total)s) would exceed the maximum \
                        allowed (%(max)s) for this agreement.",
                    total=ag.total_suspension_days_used,
                    max=ag.max_suspension_days,
                )
            )
