{
    'name': 'Viavista UI',
    'version': '1.0',
    'summary': 'Optional UI improvements with per-user toggles',
    'description': """
Optional Odoo UI enhancements that can be toggled on/off per user.

Current features:
- Show stock per warehouse on product kanban cards
  (user's default warehouse shown first, warehouses with zero stock hidden)
- Hide menu items per user (admin-only configuration)
""",
    'category': 'Productivity',
    'author': 'Viavista d.o.o.',
    'website': 'https://www.viavista.ba',
    'depends': ['stock', 'sale_stock'],
    'data': [
        'views/res_users_views.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
