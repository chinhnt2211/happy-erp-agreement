# Copyright 2025 - Happy ERP
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from markupsafe import Markup, escape

from odoo import api, fields, models
from odoo.exceptions import UserError


class Agreement(models.Model):
    _inherit = "agreement"

    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("active", "Active"),
            ("expired", "Expired"),
            ("closed", "Closed"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible",
        tracking=True,
        help="Sales employee responsible for managing this agreement.",
    )
    note = fields.Html(
        string="Notes",
        help="Notes and remarks about this agreement.",
    )

    def write(self, vals):
        res = super().write(vals)
        today = fields.Date.context_today(self)
        if vals.get("end_date") is not None:
            for rec in self:
                if rec.state == "active" and rec.end_date and rec.end_date < today:
                    rec._set_expired_and_notify()

        if vals.get("user_id"):
            for rec in self:
                if rec.user_id and rec.user_id.partner_id:
                    rec.message_subscribe(partner_ids=[rec.user_id.partner_id.id])
        return res

    def action_confirm(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.state != "draft":
                raise UserError(self.env._("Only draft agreements can be confirmed."))
            if rec.end_date and rec.end_date < today:
                rec._set_expired_and_notify()
            else:
                rec.write({"state": "active"})
        return True

    def action_close(self):
        for rec in self:
            if rec.state not in ("draft", "active", "expired"):
                raise UserError(
                    self.env._(
                        "Only draft, active or expired agreements can be closed."
                    )
                )
        self.write({"state": "closed"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True

    @api.model
    def _cron_agreement_auto_expire(self):
        today = fields.Date.context_today(self)
        agreements = self.search(
            [
                ("state", "=", "active"),
                ("end_date", "!=", False),
                ("end_date", "<", today),
            ]
        )
        for agreement in agreements:
            agreement._set_expired_and_notify()

    def _set_expired_and_notify(self):
        self.ensure_one()
        if self.state == "closed":
            return
        self.write({"state": "expired"})
        message = self.env._(
            "Agreement <strong>%(name)s</strong> "
            "[<strong>%(code)s</strong>] "
            "has expired (end date: <strong>%(end_date)s</strong>)."
        )
        body = Markup(message) % {
            "name": escape(self.name or ""),
            "code": escape(self.code or ""),
            "end_date": escape(str(self.end_date or "")),
        }
        partner_ids = []
        if self.user_id and self.user_id.partner_id:
            partner_ids = [self.user_id.partner_id.id]
        odoobot = self.env.ref("base.partner_root", raise_if_not_found=False)
        author_id = odoobot.id if odoobot else self.env.user.partner_id.id

        self.sudo().message_post(
            body=body,
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
            author_id=author_id,
            partner_ids=partner_ids,
        )

        if author_id:
            self._post_expired_to_discuss_channel(body, author_id)

    def _post_expired_to_discuss_channel(self, body, author_id):
        Channel = None
        for name in ("discuss.channel", "mail.channel"):
            try:
                Channel = self.env[name].sudo()
                break
            except KeyError:
                continue

        channel_name = "agreement-notify"
        channel = Channel.search([("name", "=", channel_name)], limit=1)
        if not channel:
            channel = Channel.create(
                {
                    "name": channel_name,
                    "channel_type": "channel",
                }
            )

        if channel:
            channel.message_post(
                body=body,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
                author_id=author_id,
            )
