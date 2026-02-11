# Copyright 2025 - Happy ERP
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Agreement Suspension",
    "summary": "The agreement validity is suspended for \
        a maximum allowed period.",
    "version": "19.0.1.0.0",
    "category": "Contract",
    "author": "Happy ERP, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["agreement"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "wizard/agreement_suspension_wizard.xml",
        "views/agreement.xml",
        "views/agreement_suspension.xml",
    ],
    "installable": True,
}
