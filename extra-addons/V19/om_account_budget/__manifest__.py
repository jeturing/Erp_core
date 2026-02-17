{
    'name': 'Odoo 17 Budget Management',
    'author': 'Odoo Mates, Odoo SA',
    'category': 'Accounting',
    'version': '19.0.1.0',
    'description': 'Use budgets to compare actual with expected revenues and costs',
    'summary': 'Odoo 17 Budget Management',
    'website': 'https://www.odoomates.tech',
    'depends': [
        'account',
    ],
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'security/account_budget_security.xml',
        'views/account_analytic_account_views.xml',
        'views/account_budget_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'images': [
        'static/description/banner.gif',
    ],
    'demo': [
        'data/account_budget_demo.xml',
    ],
}
