from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    brand_id = fields.Many2one(
        'product.brand',
        related='product_tmpl_id.brand_id',
        store=True,
        index=True,
    )

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
