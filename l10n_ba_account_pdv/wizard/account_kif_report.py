# Copyright 2026 Viavista d.o.o.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountKifReport(models.TransientModel):
    _name = "account.kif.report"
    _description = "KIF - Knjiga izlaznih faktura"

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
    line_ids = fields.One2many("account.kif.line", "report_id")

    def _get_tag_names(self, move_line):
        """Return set of tax tag names on a move line."""
        return set(move_line.tax_tag_ids.mapped("name"))

    def action_generate(self):
        self.ensure_one()
        self.line_ids.unlink()

        domain = [
            ("move_type", "in", ("out_invoice", "out_refund")),
            ("state", "=", "posted"),
            ("invoice_date", ">=", self.date_from),
            ("invoice_date", "<=", self.date_to),
            ("company_id", "=", self.company_id.id),
        ]
        moves = self.env["account.move"].search(domain, order="invoice_date, name")

        if not moves:
            raise UserError(
                _("Nema proknjiženih izlaznih faktura za odabrani period.")
            )

        lines_vals = []
        for seq, move in enumerate(moves, start=1):
            sign = -1 if move.move_type == "out_refund" else 1
            partner = move.partner_id.commercial_partner_id

            # Collect base lines and tax lines
            base_lines = move.line_ids.filtered(
                lambda l: l.tax_ids and l.display_type == "product"
            )
            tax_lines = move.line_ids.filtered(
                lambda l: l.tax_line_id
                and l.tax_line_id.type_tax_use == "sale"
            )

            # Total amounts from actual Odoo-computed values
            # Sale invoice: balance is negative (credit), so negate
            total_base = sign * sum(base_lines.mapped("balance")) * -1
            total_pdv = sign * sum(tax_lines.mapped("balance")) * -1

            # Classify base lines using tax tags from l10n_ba
            export_base = 0.0
            exempt_base = 0.0
            domestic_base = 0.0
            fc_fbih = 0.0
            fc_rs = 0.0
            fc_brcko = 0.0

            for line in base_lines:
                line_base = sign * line.balance * -1
                tags = self._get_tag_names(line)

                if "ba_out_export" in tags:
                    export_base += line_base
                elif "ba_out_exempt" in tags:
                    exempt_base += line_base
                elif "ba_out_domestic" in tags:
                    # Determine if buyer is PDV registered
                    partner_vat = partner.vat or ""
                    if partner_vat:
                        domestic_base += line_base
                    else:
                        # Final consumer — default to FBiH
                        # TODO: detect entity from partner address
                        fc_fbih += line_base
                else:
                    domestic_base += line_base

            # PDV split: registered vs final consumption
            registered_pdv = 0.0
            fc_pdv = 0.0
            partner_vat = partner.vat or ""
            if partner_vat:
                registered_pdv = total_pdv
            else:
                fc_pdv = total_pdv

            lines_vals.append({
                "report_id": self.id,
                "sequence": seq,
                "move_id": move.id,
                "invoice_date": move.invoice_date,
                "invoice_number": move.name,
                "partner_name": partner.name,
                "partner_jib": partner.l10n_ba_jib or partner.vat or "",
                "internal_amount": 0.0,
                "base_amount": total_base,
                "export_amount": export_base,
                "exempt_amount": exempt_base,
                "pdv_amount": total_pdv,
                "registered_base": domestic_base,
                "registered_pdv": registered_pdv,
                "fc_fbih": fc_fbih,
                "fc_rs": fc_rs,
                "fc_brcko": fc_brcko,
                "fc_pdv": fc_pdv,
            })

        self.env["account.kif.line"].create(lines_vals)

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
            "l10n_ba_account_pdv.action_report_kif"
        ).report_action(self)


class AccountKifLine(models.TransientModel):
    _name = "account.kif.line"
    _description = "KIF linija"
    _order = "sequence"

    report_id = fields.Many2one("account.kif.report", ondelete="cascade")
    sequence = fields.Integer()
    move_id = fields.Many2one("account.move")
    invoice_date = fields.Date()
    invoice_number = fields.Char()
    partner_name = fields.Char()
    partner_jib = fields.Char()
    # Column 6: Internal turnover
    internal_amount = fields.Float(digits=(16, 2))
    # Column 7: Invoice amount without VAT
    base_amount = fields.Float(digits=(16, 2))
    # Column 8: Export
    export_amount = fields.Float(digits=(16, 2))
    # Column 9: Other exempt supplies
    exempt_amount = fields.Float(digits=(16, 2))
    # Column 10: VAT amount
    pdv_amount = fields.Float(digits=(16, 2))
    # Column 11-12: Registered VAT payers (base + VAT)
    registered_base = fields.Float(digits=(16, 2))
    registered_pdv = fields.Float(digits=(16, 2))
    # Column 13-16: Non-registered (final consumption by entity + VAT)
    fc_fbih = fields.Float(digits=(16, 2))
    fc_rs = fields.Float(digits=(16, 2))
    fc_brcko = fields.Float(digits=(16, 2))
    fc_pdv = fields.Float(digits=(16, 2))
