# Copyright 2026 Viavista d.o.o.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountDpdvReport(models.TransientModel):
    _name = "account.dpdv.report"
    _description = "Obrazac D PDV - Dodatak uz PDV prijavu"

    date_from = fields.Date(
        required=True,
        default=lambda self: fields.Date.today().replace(day=1),
    )
    date_to = fields.Date(
        required=True,
        default=lambda self: fields.Date.today(),
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )

    generated = fields.Boolean()

    # Header
    company_name = fields.Char(compute="_compute_header", store=True)
    company_jib = fields.Char(compute="_compute_header", store=True)
    company_address = fields.Char(compute="_compute_header", store=True)

    # II. Isporuke i PDV obračunat na izlaze
    # (1) Opis  (2) Iznos bez PDV  (3) PDV obračunat na izlaze
    out_1_base = fields.Float(
        "II.1 Promet koji ne podliježe oporezivanju (čl. 3, čl. 15)",
        digits=(16, 2),
    )
    out_2_base = fields.Float(
        "II.2 Isporuke EUFOR-u i NATO", digits=(16, 2),
    )
    out_3_base = fields.Float(
        "II.3 Oslobođene isporuke - IPA fond (čl. 29)", digits=(16, 2),
    )
    out_4_base = fields.Float(
        "II.4 Usluge vezane za uvoz oslobođene PDV-a (čl. 26)",
        digits=(16, 2),
    )
    out_5_base = fields.Float(
        "II.5 Prenos imovine (čl. 7)", digits=(16, 2),
    )
    out_6_base = fields.Float(
        "II.6 Promet nekretnina - prvi prenos", digits=(16, 2),
    )
    out_6_pdv = fields.Float("II.6 PDV", digits=(16, 2))
    out_7_pdv = fields.Float(
        "II.7 PDV na usluge stranih lica (čl. 13)", digits=(16, 2),
    )
    out_8_base = fields.Float(
        "II.8 PDV vraćen stranim državljanima (PDV-SL-2)",
        digits=(16, 2),
    )
    out_8_pdv = fields.Float("II.8 PDV", digits=(16, 2))
    out_9_base = fields.Float(
        "II.9 Izdate KO kupcima u zemlji", digits=(16, 2),
    )
    out_9_pdv = fields.Float("II.9 PDV", digits=(16, 2))
    out_10_pdv = fields.Float(
        "II.10 Neplaćeni PDV po posebnoj šemi (čl. 41, 66)",
        digits=(16, 2),
    )

    # III. Nabavke i PDV obračunat na ulaze
    in_1_base = fields.Float(
        "III.1 Nabavka imovine (čl. 7)", digits=(16, 2),
    )
    in_2_base = fields.Float(
        "III.2 Nabavka nekretnina s pravom odbitka", digits=(16, 2),
    )
    in_2_pdv = fields.Float("III.2 PDV", digits=(16, 2))
    in_3_base = fields.Float(
        "III.3 Nabavka opreme s pravom odbitka - domaća", digits=(16, 2),
    )
    in_3_pdv = fields.Float("III.3 PDV", digits=(16, 2))
    in_4_base = fields.Float(
        "III.4 Nabavka opreme s pravom odbitka - uvoz", digits=(16, 2),
    )
    in_4_pdv = fields.Float("III.4 PDV", digits=(16, 2))
    in_5_base = fields.Float(
        "III.5 Proporcionalni odbitak (čl. 37)", digits=(16, 2),
    )
    in_5_pdv = fields.Float("III.5 PDV", digits=(16, 2))
    in_6_base = fields.Float(
        "III.6 Usluge iz inostranstva s pravom odbitka", digits=(16, 2),
    )
    in_6_pdv = fields.Float("III.6 PDV", digits=(16, 2))
    in_7_pdv = fields.Float(
        "III.7 PDV po posebnoj šemi u građevinarstvu (čl. 42)",
        digits=(16, 2),
    )
    in_8_base = fields.Float(
        "III.8 Primljene KO od dobavljača", digits=(16, 2),
    )
    in_8_pdv = fields.Float("III.8 PDV", digits=(16, 2))
    in_9_pdv = fields.Float(
        "III.9 Ispravka odbitka ulaznog PDV-a (čl. 36)", digits=(16, 2),
    )

    # IV. Zalihe
    stock_value = fields.Float(
        "IV.1 Stanje zaliha na kraju perioda (bez PDV)", digits=(16, 2),
    )

    @api.depends("company_id")
    def _compute_header(self):
        for rec in self:
            partner = rec.company_id.partner_id
            rec.company_name = partner.name or ""
            rec.company_jib = (
                partner.l10n_ba_jib or partner.vat or ""
            )
            rec.company_address = ", ".join(
                filter(None, [partner.street, partner.zip, partner.city])
            )

    def action_generate(self):
        """Generate D PDV data.

        Most fields in D PDV require detailed tax/product category
        classification that goes beyond basic tax tags. This generates
        a form with zeros that the accountant fills in manually based
        on their detailed records. Fields that can be auto-populated
        from tax tags are filled where possible.
        """
        self.ensure_one()
        # D PDV fields require granular classification not available
        # from standard tax tags. Provide the form for manual entry.
        # Future: extend with product category / account-based detection.
        self.generated = True
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_print_pdf(self):
        self.ensure_one()
        return self.env.ref(
            "l10n_ba_account_pdv.action_report_dpdv"
        ).report_action(self)
