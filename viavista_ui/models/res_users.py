from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    show_stock_per_warehouse = fields.Boolean(
        string='Show Stock per Warehouse',
        help='Display per-warehouse stock quantities on product kanban cards '
             'instead of total on-hand quantity.',
    )
    hidden_menu_ids = fields.Many2many(
        'ir.ui.menu', string='Hidden Menus',
        help='Menu items hidden for this user. Admin users are not affected.',
    )

    def write(self, vals):
        res = super().write(vals)
        if 'hidden_menu_ids' in vals:
            self.env.registry.clear_cache()
        return res

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['show_stock_per_warehouse']

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ['show_stock_per_warehouse']
