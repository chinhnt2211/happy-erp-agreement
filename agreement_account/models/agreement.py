# Copyright 2017-2020 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class Agreement(models.Model):
    _inherit = "agreement"

    invoice_ids = fields.One2many(
        "account.move", "agreement_id", string="Invoices", readonly=True
    )
    out_invoice_count = fields.Integer(
        compute="_compute_invoice_count", string="# Invoices"
    )
    in_invoice_count = fields.Integer(
        compute="_compute_invoice_count", string="# Vendor Bills"
    )

    def _compute_invoice_count(self):
        # Only query DB for existing records; new/virtual records get 0
        existing = self.exists()
        for agreement in self:
            if agreement not in existing:
                agreement.out_invoice_count = 0
                agreement.in_invoice_count = 0
        if not existing:
            return
        aio = self.env["account.move"]
        base_domain = [("agreement_id", "in", existing.ids)]
        out_rg_res = aio.formatted_read_group(
            base_domain + [("move_type", "in", ("out_invoice", "out_refund"))],
            groupby=["agreement_id"],
            aggregates=["__count"],
        )
        out_data = {item["agreement_id"][0]: item["__count"] for item in out_rg_res}
        in_rg_res = aio.formatted_read_group(
            base_domain + [("move_type", "in", ("in_invoice", "in_refund"))],
            groupby=["agreement_id"],
            aggregates=["__count"],
        )
        in_data = {item["agreement_id"][0]: item["__count"] for item in in_rg_res}
        for agreement in existing:
            agreement.out_invoice_count = out_data.get(agreement.id, 0)
            agreement.in_invoice_count = in_data.get(agreement.id, 0)
