{
    'name': 'Viavista Blog',
    'version': '1.0',
    'summary': 'Consistent blog cover image display and per-device visibility',
    'description': """
Blog cover image improvements for Odoo 19.

**Consistent cover display:** Replaces fixed viewport-height sizing with CSS
aspect-ratio so the cover image maintains consistent proportions across desktop,
tablet, and mobile — eliminating the cropping differences between devices.

**Per-device visibility:** Adds a "Visibility" option to the blog cover settings
(desktop only, mobile only, or hidden). Hidden covers still appear as thumbnails
on the blog list page. In the editor, hidden covers show in the Invisible Elements
panel, matching standard Odoo block behavior.
""",
    'category': 'Website/Website',
    'author': 'Viavista d.o.o.',
    'website': 'https://www.viavista.ba',
    'depends': ['website_blog'],
    'assets': {
        'web.assets_frontend': [
            'viavista_blog/static/src/scss/blog_cover.scss',
        ],
        'website.website_builder_assets': [
            'viavista_blog/static/src/website_builder/**/*',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
