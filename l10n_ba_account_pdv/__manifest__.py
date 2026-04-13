# Copyright 2026 Viavista d.o.o.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "BiH - PDV izvještaji",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations",
    "summary": "KIF, KUF, Obrazac P PDV i D PDV za Bosnu i Hercegovinu",
    "author": "Viavista d.o.o., Odoo Community Association (OCA)",
    "website": "https://github.com/viavista/viavista-odoo-modules",
    "license": "AGPL-3",
    "development_status": "Alpha",
    "maintainers": ["vv-zgalic"],
    "depends": [
        "l10n_ba",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/account_kif_template.xml",
        "report/account_kuf_template.xml",
        "report/account_pdv_template.xml",
        "report/account_dpdv_template.xml",
        "views/account_kif_views.xml",
        "views/account_kuf_views.xml",
        "views/account_pdv_views.xml",
        "views/account_dpdv_views.xml",
        "views/menu_views.xml",
    ],
    "installable": True,
}
