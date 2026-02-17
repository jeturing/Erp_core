{
    'name': 'Open HRMS Reminders Todo',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'HR Reminder For OHRMS',
    'description': """This module is a powerful and easy-to-use tool that can 
    help you improve your HR processes and ensure that important events are 
    never forgotten.""",
    'author': 'Cybrosys Techno solutions,Open HRMS',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.openhrms.com',
    'live_test_url': 'https://youtu.be/tOG92cMa4Rg',
    'depends': [
        'hr',
    ],
    'data': [
        'security/hr_reminder_security.xml',
        'security/ir.model.access.csv',
        'views/hr_reminder_views.xml',
    ],
    'assets': {'web.assets_backend': ['hr_reminder/static/src/css/notification.css', 'hr_reminder/static/src/scss/reminder.scss', 'hr_reminder/static/src/xml/reminder_topbar.xml', 'hr_reminder/static/src/js/reminder_topbar.js']},
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
