{
    'name': 'Automatic Invoice And Post',
    'version': '19.0.1.0.1',
    'category': 'Sales,Warehouse,Accounting',
    'summary': ' Auto Invoice Generation and Auto Sending of Invoice on 
     Delivery validation.',
    'description': 'This module generates and post invoice  while validating 
    the delivery and enable to send invoice to customer
     on delivery validate .',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'base',
        'sale_management',
        'stock',
        'account',
    ],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'license': 'AGPL-3',
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
