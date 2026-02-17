{
    'name': 'Advanced Dynamic Dashboard',
    'version': '19.0.1.2.0',
    'category': 'Productivity',
    'summary': 'Create Configurable Dashboards Easily',
    'description': 'Create Configurable Advanced Dynamic Dashboard to get the 
    information that are relevant to your business, department, or a specific 
    process or need',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/dashboard_theme_data.xml',
        'views/dashboard_views.xml',
        'views/dynamic_block_views.xml',
        'views/dashboard_menu_views.xml',
        'views/dashboard_theme_views.xml',
        'wizard/dashboard_mail_views.xml',
    ],
    'assets': {'web.assets_backend': ['advanced_dynamic_dashboard/static/src/css/**/*.css', 'advanced_dynamic_dashboard/static/src/scss/**/*.scss', 'advanced_dynamic_dashboard/static/src/js/**/*.js', 'advanced_dynamic_dashboard/static/src/xml/**/*.xml', 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css', 'advanced_dynamic_dashboard/static/lib/js/interactjs.js']},
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
    'uninstall_hook': 'uninstall_hook',
}
