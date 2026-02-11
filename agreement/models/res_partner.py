# Copyright (C) 2018 - TODAY, Pavlov Media
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    agreement_ids = fields.One2many("agreement", "partner_id", string="Agreements")
    agreements_count = fields.Integer(compute="_compute_agreements_count")

    @api.depends("agreement_ids")
    def _compute_agreements_count(self):
        # Always assign a value (including for <NewId ...> records during onchanges)
        for rec in self:
            rec.agreements_count = 0

        partners = self.filtered(lambda p: p.id)
        if not partners:
            return

        fetch_data = self.env["agreement"].formatted_read_group(
            domain=[("partner_id", "in", partners.ids)],
            groupby=["partner_id"],
            aggregates=["__count"],
        )
        agreement_dict = {item["partner_id"][0]: item["__count"] for item in fetch_data}
        for rec in partners:
            rec.agreements_count = agreement_dict.get(rec.id, 0)

    def action_open_agreement(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "agreement.agreement_action"
        )
        action["domain"] = [("partner_id", "=", self.id)]
        action["context"] = {"default_partner_id": self.id}
        return action
