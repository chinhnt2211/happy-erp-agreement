# Copyright 2025 - Happy ERP
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Agreement Management",
    "summary": "Lifecycle, responsible user, notes and auto-expiration for agreements",
    "version": "19.0.1.0.0",
    "category": "Contract",
    "author": "Happy ERP, Odoo Community Association (OCA)",
    "website": "https://github.com/happy-erp/happy-erp-agreement",
    "license": "AGPL-3",
    "depends": ["agreement", "mail"],
    "data": [
        "data/ir_cron.xml",
        "views/agreement_views.xml",
    ],
    "installable": True,
}
