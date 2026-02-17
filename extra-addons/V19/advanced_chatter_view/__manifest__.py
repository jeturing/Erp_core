{
    'name': 'Advanced Chatter View',
    'version': '19.0.1.0.1',
    'category': 'Discuss',
    'summary': 'Advanced odoo chatter view.',
    'description': 'This module is used to view advanced chatter.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'base',
        'mail',
    ],
    'assets': {'web.assets_backend': ['https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.3/font/bootstrap-icons.css', 'advanced_chatter_view/static/src/css/chatter_topbar.css', 'advanced_chatter_view/static/src/js/chatter_container.js', 'advanced_chatter_view/static/src/xml/chatter.xml']},
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
