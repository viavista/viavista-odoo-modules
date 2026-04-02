# Copyright 2026 Viavista d.o.o.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "BIH - Finansijski izvještaji",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations",
    "summary": "Bilanca stanja i RDG prema FIA standardima za Bosnu i Hercegovinu",
    "author": "Viavista d.o.o., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-ba",
    "license": "AGPL-3",
    "development_status": "Alpha",
    "maintainers": ["zvone187"],
    "depends": [
        "l10n_ba",
    ],
    "data": [
        "data/account_bilanca_stanja_report.xml",
        "data/account_rdg_report.xml",
    ],
    "installable": True,
}
