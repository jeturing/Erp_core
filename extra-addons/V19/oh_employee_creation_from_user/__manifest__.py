{
    'name': 'Open HRMS Employees From User',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Automatically creates employee while creating user',
    'description': 'This module facilitates the automatic creation of employee records when users are being created.',
    'author': 'Cybrosys Techno Solutions, Open HRMS',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.openhrms.com',
    'depends': [
        'hr',
    ],
    'data': [
        'views/res_users_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
