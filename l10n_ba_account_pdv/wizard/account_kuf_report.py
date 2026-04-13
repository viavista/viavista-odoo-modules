# Copyright 2026 Viavista d.o.o.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountKufReport(models.TransientModel):
    _name = "account.kuf.report"
    _description = "KUF - Knjiga ulaznih faktura"

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
    line_ids = fields.One2many("account.kuf.line", "report_id")

    def action_generate(self):
        self.ensure_one()
        self.line_ids.unlink()

        domain = [
            ("move_type", "in", ("in_invoice", "in_refund")),
            ("state", "=", "posted"),
            ("invoice_date", ">=", self.date_from),
            ("invoice_date", "<=", self.date_to),
            ("company_id", "=", self.company_id.id),
        ]
        moves = self.env["account.move"].search(domain, order="invoice_date, name")

        if not moves:
            raise UserError(
                _("Nema proknjiženih ulaznih faktura za odabrani period.")
            )

        lines_vals = []
        for seq, move in enumerate(moves, start=1):
            sign = -1 if move.move_type == "in_refund" else 1
            partner = move.partner_id.commercial_partner_id

            base_lines = move.line_ids.filtered(
                lambda l: l.tax_ids and l.display_type == "product"
            )
            tax_lines = move.line_ids.filtered(
                lambda l: l.tax_line_id
                and l.tax_line_id.type_tax_use == "purchase"
            )

            # Purchase invoice: balance is positive (debit)
            total_base = sign * sum(base_lines.mapped("balance"))
            total_pdv = sign * sum(tax_lines.mapped("balance"))
            total_with_pdv = total_base + total_pdv

            # Split deductible vs non-deductible using tax tags
            deductible_pdv = 0.0
            non_deductible_pdv = 0.0

            for tl in tax_lines:
                amount = sign * tl.balance
                tag_names = set(tl.tax_tag_ids.mapped("name"))
                # Non-deductible tax has no input VAT tags
                if tag_names & {
                    "ba_in_domestic", "ba_in_import", "ba_in_rc",
                }:
                    deductible_pdv += amount
                else:
                    non_deductible_pdv += amount

            lines_vals.append({
                "report_id": self.id,
                "sequence": seq,
                "move_id": move.id,
                "invoice_date": move.invoice_date,
                "invoice_number": move.ref or move.name,
                "partner_name": partner.name,
                "partner_jib": partner.l10n_ba_jib or partner.vat or "",
                "base_amount": total_base,
                "total_with_pdv": total_with_pdv,
                "flat_rate_amount": 0.0,
                "total_input_pdv": total_pdv,
                "deductible_pdv": deductible_pdv,
                "non_deductible_pdv": non_deductible_pdv,
                "non_pdv_purchase": 0.0,
                "compensation_value": 0.0,
                "farmer_rate": 0.0,
            })

        self.env["account.kuf.line"].create(lines_vals)

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
            "l10n_ba_account_pdv.action_report_kuf"
        ).report_action(self)


class AccountKufLine(models.TransientModel):
    _name = "account.kuf.line"
    _description = "KUF linija"
    _order = "sequence"

    report_id = fields.Many2one("account.kuf.report", ondelete="cascade")
    sequence = fields.Integer()
    move_id = fields.Many2one("account.move")
    invoice_date = fields.Date()
    # Column 2: Vendor invoice number (ref)
    invoice_number = fields.Char()
    # Column 4: Supplier name
    partner_name = fields.Char()
    # Column 5: Supplier JIB
    partner_jib = fields.Char()
    # Column 6: Invoice amount without VAT
    base_amount = fields.Float(digits=(16, 2))
    # Column 7: Invoice amount with VAT
    total_with_pdv = fields.Float(digits=(16, 2))
    # Column 8: Flat-rate amount (paušal)
    flat_rate_amount = fields.Float(digits=(16, 2))
    # Column 9: Total input VAT
    total_input_pdv = fields.Float(digits=(16, 2))
    # Column 10: Deductible input VAT
    deductible_pdv = fields.Float(digits=(16, 2))
    # Column 11: Non-deductible input VAT
    non_deductible_pdv = fields.Float(digits=(16, 2))
    # Column 12: Purchase from non-VAT payers
    non_pdv_purchase = fields.Float(digits=(16, 2))
    # Column 13: Compensation value received
    compensation_value = fields.Float(digits=(16, 2))
    # Column 14: Farmer flat-rate 5% (čl. 85)
    farmer_rate = fields.Float(digits=(16, 2))
