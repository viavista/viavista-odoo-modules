{
    'name': 'Script Runner',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': 'Run Python scripts from within Odoo',
    'description': 'Execute Python scripts with parameter support, async execution, and full audit logging.',
    'author': 'Viavista d.o.o.',
    'website': 'https://viavista.ba',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/script_run_wizard_views.xml',
        'views/script_views.xml',
        'views/execution_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'viavista_script_runner/static/src/js/execution_auto_refresh.js',
            'viavista_script_runner/static/src/xml/execution_auto_refresh.xml',
        ],
    },
    'uninstall_hook': '_uninstall_hook',
    'installable': True,
    'license': 'LGPL-3',
    'application': False,
}
