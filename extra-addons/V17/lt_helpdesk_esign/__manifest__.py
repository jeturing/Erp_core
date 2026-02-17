##############################################################################
# Copyright (c) 2022 lumitec GmbH (https://www.lumitec.solutions)
# All Right Reserved
#
# See LICENSE file for full licensing details.
##############################################################################
{
    'name': ' Simplify Helpdesk Operations: Send Documents via E-Sign',
    'summary': 'Simplify Helpdesk Operations: Send Documents via E-Sign ',
    'author': "lumitec GmbH",
    'website': "https://www.lumitec.solutions",
    'category': 'Services/Helpdesk ',
    'version': '17.0.1.0.0',
    'license': 'OPL-1',
    'images': ['static/description/thumbnail.png'],
    'depends': [
        'base',
        'helpdesk',
        'sign',
    ],
    'data': [
        'data/cron.xml',
        'views/helpdesk_ticket.xml',
        'views/send_sign_request.xml',
        'views/sign_request.xml',
        'views/sign_template.xml',
         ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
