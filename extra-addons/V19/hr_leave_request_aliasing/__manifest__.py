{
    'name': 'Open HRMS Leave Request Aliasing',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Automated Leave Request generation from Incoming Emails.',
    'description': """This module simplifies leave request creation by 
     seamlessly generating requests from incoming emails, making the process 
     efficient, saving time, and enhancing employee experience.""",
    'live_test_url': 'https://youtu.be/jQFAP20k_Wc',
    'author': 'Cybrosys Techno solutions, Open HRMS',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.openhrms.com',
    'depends': [
        'hr_holidays',
    ],
    'data': [
        'data/mail_alias_data.xml',
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
