{
    'name': 'All In One Google Analytics',
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'summary': 'By connecting Google Analytics to Odoo and tracking relevant events, you can make data-driven decisions, improve userexperience, and enhance the overall performance of your application.',
    'description': 'Integrating Odoo with Google Analytics allows businesses totrack user interactions and events within the Odoo application and send that data to their Google Analytics account.This integration empowers businesses to improve user experience and overall application performance.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'sale_management',
        'purchase',
        'account',
        'website_sale',
    ],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
