# Copyright 2026 Viavista d.o.o.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountPdvReport(models.TransientModel):
    _name = "account.pdv.report"
    _description = "Obrazac P PDV - PDV prijava"

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
    company_zip_city = fields.Char(compute="_compute_header", store=True)

    # I. Isporuke i nabavke (bez PDV-a)
    # IZLAZI
    field_11 = fields.Float("r.11 Isporuke", digits=(16, 2))
    field_12 = fields.Float("r.12 Vrijednost izvoza", digits=(16, 2))
    field_13 = fields.Float("r.13 Oslobođene isporuke", digits=(16, 2))
    # ULAZI
    field_21 = fields.Float("r.21 Sve nabavke", digits=(16, 2))
    field_22 = fields.Float("r.22 Vrijednost uvoza", digits=(16, 2))
    field_23 = fields.Float("r.23 Nabavke od poljoprivrednika", digits=(16, 2))

    # II. PDV
    field_41 = fields.Float(
        "r.41 Ulazni PDV od registrovanih obveznika", digits=(16, 2),
    )
    field_42 = fields.Float("r.42 PDV na uvoz", digits=(16, 2))
    field_43 = fields.Float(
        "r.43 Paušalna naknada za poljoprivrednike", digits=(16, 2),
    )
    field_51 = fields.Float("r.51 Izlazni PDV", digits=(16, 2))
    field_61 = fields.Float(
        "r.61 Ulazni PDV ukupno", digits=(16, 2),
        compute="_compute_totals", store=True,
    )
    field_71 = fields.Float(
        "r.71 Iznos za uplatu/povrat", digits=(16, 2),
        compute="_compute_totals", store=True,
    )

    # III. Krajnja potrošnja
    field_32 = fields.Float("r.32 Federacija BiH", digits=(16, 2))
    field_33 = fields.Float("r.33 Republika Srpska", digits=(16, 2))
    field_34 = fields.Float("r.34 Brčko Distrikt", digits=(16, 2))

    field_80 = fields.Boolean("r.80 Zahtjev za povrat")

    @api.depends("company_id")
    def _compute_header(self):
        for rec in self:
            partner = rec.company_id.partner_id
            rec.company_name = partner.name or ""
            rec.company_jib = (
                partner.l10n_ba_jib or partner.vat or ""
            )
            rec.company_address = partner.street or ""
            rec.company_zip_city = " ".join(
                filter(None, [partner.zip, partner.city])
            )

    @api.depends("field_41", "field_42", "field_43", "field_51")
    def _compute_totals(self):
        for rec in self:
            rec.field_61 = rec.field_41 + rec.field_42 + rec.field_43
            rec.field_71 = rec.field_51 - rec.field_61

    def _find_tag(self, tag_name):
        """Find a tax tag by exact name for country BA."""
        return self.env["account.account.tag"].search(
            [
                ("name", "=", tag_name),
                ("applicability", "=", "taxes"),
                ("country_id.code", "=", "BA"),
            ],
            limit=1,
        )

    def _get_tagged_balance(self, tag_name, repartition_type=None):
        """Sum move line balances for a tax tag, optionally filtered by
        repartition type ('base' or 'tax').

        Returns absolute value.
        """
        tag = self._find_tag(tag_name)
        if not tag:
            return 0.0

        domain = [
            ("parent_state", "=", "posted"),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
            ("company_id", "=", self.company_id.id),
            ("tax_tag_ids", "in", tag.ids),
        ]
        if repartition_type == "base":
            # Base lines have tax_ids set but no tax_line_id
            domain.append(("tax_line_id", "=", False))
        elif repartition_type == "tax":
            # Tax lines have tax_line_id set
            domain.append(("tax_line_id", "!=", False))

        result = self.env["account.move.line"].read_group(
            domain, ["balance"], [],
        )
        return abs(result[0]["balance"]) if result else 0.0

    def action_generate(self):
        self.ensure_one()

        # I. Output base amounts (base repartition only)
        self.field_11 = self._get_tagged_balance(
            "ba_out_domestic", repartition_type="base",
        )
        self.field_12 = self._get_tagged_balance(
            "ba_out_export", repartition_type="base",
        )
        self.field_13 = self._get_tagged_balance(
            "ba_out_exempt", repartition_type="base",
        )

        # I. Input base amounts (base repartition only)
        self.field_21 = self._get_tagged_balance(
            "ba_in_domestic", repartition_type="base",
        )
        self.field_22 = self._get_tagged_balance(
            "ba_in_import", repartition_type="base",
        )
        self.field_23 = 0.0  # TODO: farmer flat-rate tag

        # II. PDV amounts (tax repartition only)
        self.field_51 = self._get_tagged_balance("ba_output_vat")
        self.field_41 = self._get_tagged_balance(
            "ba_in_domestic", repartition_type="tax",
        )
        self.field_42 = self._get_tagged_balance(
            "ba_in_import", repartition_type="tax",
        )
        self.field_43 = 0.0  # TODO: farmer flat-rate

        # III. Final consumption by entity
        # TODO: requires entity-level tags on taxes
        self.field_32 = 0.0
        self.field_33 = 0.0
        self.field_34 = 0.0

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
            "l10n_ba_account_pdv.action_report_pdv"
        ).report_action(self)
