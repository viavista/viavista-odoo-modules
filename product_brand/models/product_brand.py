from odoo import fields, models


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'Product Brand'
    _inherit = ['image.mixin']
    _order = 'name'

    name = fields.Char(required=True, translate=True)
