from odoo import api, models


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def _visible_menu_ids(self, debug=False):
        visible = super()._visible_menu_ids(debug=debug)
        user = self.env.user
        if user.has_group('base.group_system'):
            return visible
        hidden = user.hidden_menu_ids
        if not hidden:
            return visible
        # Collect hidden menu IDs + all their descendants
        hidden_ids = set(hidden.ids)
        all_menus = self.sudo().search([('id', 'in', list(visible))])
        for menu in all_menus:
            parent = menu.parent_id
            while parent:
                if parent.id in hidden_ids:
                    hidden_ids.add(menu.id)
                    break
                parent = parent.parent_id
        return visible - hidden_ids
