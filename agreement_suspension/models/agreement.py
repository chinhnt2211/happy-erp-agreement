# Copyright 2025 - Happy ERP
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class Agreement(models.Model):
    _inherit = "agreement"

    max_suspension_days = fields.Integer(
        string="Max suspension days",
        help="Maximum total days this agreement can be suspended. \
        Leave 0 for no limit.",
        tracking=True,
    )
    suspension_ids = fields.One2many(
        "agreement.suspension",
        "agreement_id",
        string="Suspensions",
        readonly=True,
    )
    suspension_count = fields.Integer(
        compute="_compute_suspension_count",
        string="# Suspensions",
    )
    suspension_state = fields.Selection(
        selection=[
            ("normal", "Normal"),
            ("suspended", "Suspended"),
        ],
        compute="_compute_suspension_state",
        string="Suspension status",
        store=True,
    )
    total_suspension_days_used = fields.Integer(
        compute="_compute_total_suspension_days_used",
        string="Total suspension days used",
    )

    @api.depends(
        "suspension_ids",
        "suspension_ids.date_start",
        "suspension_ids.date_end",
        "suspension_ids.actual_end_date",
    )
    def _compute_total_suspension_days_used(self):
        for rec in self:
            total = 0
            for s in rec.suspension_ids:
                if s.date_start:
                    end = s.actual_end_date or s.date_end
                    if end:
                        total += (end - s.date_start).days + 1
            rec.total_suspension_days_used = total

    @api.depends("suspension_ids")
    def _compute_suspension_count(self):
        for rec in self:
            rec.suspension_count = len(rec.suspension_ids)

    @api.depends("suspension_ids.state")
    def _compute_suspension_state(self):
        for rec in self:
            if rec.suspension_ids.filtered(lambda s: s.state == "active"):
                rec.suspension_state = "suspended"
            else:
                rec.suspension_state = "normal"
