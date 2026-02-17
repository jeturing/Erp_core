{
    'name': 'Open HRMS Branch Transfer',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Employee transfer between branches',
    'description': 'This modules allows the user to transfer an employee from one branch to another branch',
    'live_test_url': 'https://youtu.be/Qva8kW6xn4c',
    'author': 'Cybrosys Techno solutions,Open HRMS',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://cybrosys.com, https://www.openhrms.com',
    'depends': [
        'hr',
        'hr_contract',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_employee_security.xml',
        'views/employee_transfer_views.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
