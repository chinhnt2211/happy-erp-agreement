# Copyright 2017-2020 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestAgreementAccount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.test_customer = cls.env["res.partner"].create({"name": "TestCustomer"})
        cls.test_agreement_sale = cls.env["agreement"].create(
            {
                "name": "TestAgreement-Sale",
                "code": "SALE",
                "partner_id": cls.test_customer.id,
                "domain": "sale",
            }
        )
        cls.test_agreement_purchase = cls.env["agreement"].create(
            {
                "name": "TestAgreement-Purchase",
                "code": "PURCHASE",
                "partner_id": cls.test_customer.id,
                "domain": "purchase",
            }
        )

    def test_compute_invoice_count(self):
        self.test_agreement_sale._compute_invoice_count()
        self.test_agreement_purchase._compute_invoice_count()
