from odoo import api, fields, models


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'Product Brand'
    _inherit = ['image.mixin']
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    product_count = fields.Integer(compute='_compute_product_count')

    @api.depends()
    def _compute_product_count(self):
        data = {
            brand.id: count
            for brand, count in self.env['product.template']._read_group(
                domain=[('brand_id', 'in', self.ids)],
                groupby=['brand_id'],
                aggregates=['__count'],
            )
        }
        for brand in self:
            brand.product_count = data.get(brand.id, 0)

    def action_view_products(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'product.template',
            'view_mode': 'list,kanban,form',
            'domain': [('brand_id', '=', self.id)],
            'context': {'default_brand_id': self.id},
        }
