{
    'name': 'Open HRMS Employee Shift',
    'version': '19.0.1.0.0',
    'summary': 'Easily create, manage, and track employee shift schedules.',
    'description': 'Easily create, manage, and track employee shift schedules.',
    'live_test_url': 'https://youtu.be/o580wqD9Nig',
    'category': 'Human Resource',
    'author': 'Cybrosys Techno solutions,Open HRMS',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.openhrms.com',
    'depends': [
        'hr_payroll_community',
        'resource',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_employee_shift_security.xml',
        'views/hr_employee_shift_views.xml',
        'views/hr_employee_contract_views.xml',
        'wizard/hr_generate_shift_views.xml',
    ],
    'demo': [
        'demo/shift_schedule_data.xml',
    ],
    'assets': {'web.assets_backend': ['hr_employee_shift/static/src/css/shift_dashboard.css', 'hr_employee_shift/static/src/less/shift_dashboard.less']},
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
