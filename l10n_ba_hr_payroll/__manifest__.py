# Copyright 2026 Viavista d.o.o.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "BIH - Obračun plaća",
    "version": "19.0.1.0.0",
    "category": "Human Resources/Localizations",
    "summary": "Pravila obračuna plaća i izvještaji za Bosnu i Hercegovinu (FBiH)",
    "author": "Viavista d.o.o., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-ba",
    "license": "AGPL-3",
    "development_status": "Alpha",
    "maintainers": ["zvone187"],
    "depends": [
        "l10n_ba",
        "hr_payroll",
        "hr_work_entry_holidays",
        "hr_payroll_holidays",
    ],
    "external_dependencies": {
        "python": ["xlsxwriter"],
    },
    "data": [
        "security/ir.model.access.csv",
        "data/hr_salary_rule_data.xml",
    ],
    "installable": True,
}
