from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    warehouse_stock_display = fields.Char(
        compute='_compute_warehouse_stock_display',
        string='Stock per Warehouse',
    )

    @api.depends_context('uid')
    def _compute_warehouse_stock_display(self):
        user = self.env.user
        if not user.show_stock_per_warehouse:
            for rec in self:
                rec.warehouse_stock_display = False
            return

        warehouses = self.env['stock.warehouse'].search([
            ('company_id', 'in', self.env.companies.ids),
        ])
        if not warehouses:
            for rec in self:
                rec.warehouse_stock_display = False
            return

        # User's default warehouse first
        user_wh = user.property_warehouse_id
        if user_wh and user_wh in warehouses:
            wh_order = user_wh + (warehouses - user_wh)
        else:
            wh_order = warehouses

        storable = self.filtered('is_storable')
        non_storable = self - storable
        for rec in non_storable:
            rec.warehouse_stock_display = False

        if not storable:
            return

        # Read qty per warehouse — one batch read per warehouse
        wh_data = {}  # {template_id: [(wh_code, qty), ...]}
        for wh in wh_order:
            qty_map = {
                d['id']: d['qty_available']
                for d in storable.with_context(warehouse_id=wh.id).read(['qty_available'])
            }
            for tmpl_id, qty in qty_map.items():
                if qty > 0:
                    wh_data.setdefault(tmpl_id, []).append((wh.code, qty))

        for rec in storable:
            parts = wh_data.get(rec.id)
            if parts:
                rec.warehouse_stock_display = '\n'.join(
                    f'{code}: {qty:g}' for code, qty in parts
                )
            else:
                rec.warehouse_stock_display = False
