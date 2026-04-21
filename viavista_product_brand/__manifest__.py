{
    'name': 'Product Brand',
    'version': '19.0.2.0.2',
    'summary': 'Organize products by brand: logos, filters, archive, and optional brand prefix in product names',
    'category': 'Sales',
    'author': 'Viavista d.o.o.',
    'website': 'https://www.viavista.ba',
    'support': 'info@viavista.ba',
    'depends': ['sale_management'],
    'images': ['images/main_screenshot.png'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_brand_views.xml',
        'views/product_template_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'demo': [
        'demo/product_brand_demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
