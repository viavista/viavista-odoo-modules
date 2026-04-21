from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    brand_id = fields.Many2one('product.brand', string='Brand', index=True)

    @api.depends('brand_id')
    def _compute_display_name(self):
        super()._compute_display_name()
        fmt = self.env['ir.config_parameter'].sudo().get_param(
            'viavista_product_brand.sale_format', 'no',
        )
        if fmt == 'no':
            return
        for rec in self:
            if not rec.brand_id or not rec.display_name:
                continue
            brand = rec.brand_id.sudo().name
            if fmt == 'bracket':
                rec.display_name = f'[{brand}] {rec.display_name}'
            elif fmt == 'dash':
                rec.display_name = f'{brand} - {rec.display_name}'
            elif fmt == 'space':
                rec.display_name = f'{brand} {rec.display_name}'
