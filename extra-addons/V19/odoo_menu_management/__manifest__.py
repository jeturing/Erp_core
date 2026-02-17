{
    'name': 'Advanced Menu Management',
    'version': '19.0.1.0.4',
    'category': 'Extra Tools',
    'author': 'faOtools',
    'website': 'https://faotools.com/apps/17.0/advanced-menu-management-17-0-odoo-menu-management-859',
    'license': 'Other proprietary',
    'application': True,
    'installable': True,
    'auto_install': False,
    'depends': [
        'web',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/ir_ui_menu.xml',
        'views/res_users.xml',
    ],
    'assets': {'web.assets_backend': ['odoo_menu_management/static/src/components/**/*.xml', 'odoo_menu_management/static/src/components/**/*.js', 'odoo_menu_management/static/src/components/**/*.scss']},
    'demo': [
    ],
    'external_dependencies': {},
    'summary': 'The tool to efficiently hide and show menus for Odoo users, companies, and security groups. User-wise menus. Company-wise menus. Delete menus. Invisible menus. Hide submenu. Multi Company Hide Any Menu For Any User. Remove submenu. Hidden menus. Limited menus. Limited access to menus. Access rights to menus. Remove menus. Hide menu from users. Hide menu from companies. Hide menus for user groups. Hide menus for users. Hide menus for companies. Disable menus for users. Disable menus for companies.',
    'description': """For the full details look at static/description/index.html
* Features * 
#odootools_proprietary""",
    'images': [
        'static/description/main.png',
    ],
    'price': '48.0',
    'currency': 'EUR',
    'live_test_url': 'https://faotools.com/my/tickets/newticket?&url_app_id=148&ticket_version=17.0&url_type_id=3',
}
