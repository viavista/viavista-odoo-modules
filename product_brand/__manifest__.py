{
    'name': 'Product Brand',
    'version': '19.0.1.0.0',
    'summary': 'Add brand to products',
    'category': 'Sales',
    'author': 'Viavista d.o.o.',
    'website': 'https://www.viavista.ba',
    'support': 'info@viavista.ba',
    'depends': ['sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_brand_views.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
