{
    'name': 'Open HRMS Resignation',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Manages the resignation process of the employees',
    'description': """This module helps to create and 
     approve/reject employee resignation requests""",
    'author': 'Cybrosys Techno solutions,Open HRMS',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.openhrms.com',
    'depends': [
        'hr',
        'hr_employee_updation',
        'mail',
        'hr_contract',
    ],
    'data': [
        'security/hr_resignation_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'views/hr_employee_views.xml',
        'views/hr_resignation_views.xml',
    ],
    'live_test_url': 'https://youtu.be/BorJthxY_VI',
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
