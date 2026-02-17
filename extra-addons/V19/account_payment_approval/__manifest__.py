{
    'name': 'Payment Approvals',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'summary': ' This modules Enables to use the approval feature in
                    customer and vendor payments.',
    'description': 'This modules enables approval feature in the payment.
     as Approval stage .Approval feature can be applied based on the given 
     amount. ',
    'author': ' Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'account',
    ],
    'data': [
        'views/res_config_settings_views.xml',
        'views/account_payment_views.xml',
    ],
    'license': 'LGPL-3',
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
