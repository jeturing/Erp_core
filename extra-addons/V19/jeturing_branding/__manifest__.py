# -*- coding: utf-8 -*-
# Part of Jeturing. See LICENSE file for full copyright and licensing details.
{
    'name': 'Jeturing Branding',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'Replace Odoo branding with Jeturing/Sajet branding across the platform',
    'description': """
Jeturing Branding Module (Odoo 19)
===================================
Replaces all visible Odoo branding with Jeturing branding:
- Footer: "Powered by Jeturing" with logo
- Login page: Jeturing branding
- Browser tab title: "Sajet" instead of "Odoo"
- Error dialogs: "Sajet" instead of "Odoo"
- Website footer: jeturing.com links
- HTTP error pages: Jeturing Support contact
    """,
    'author': 'Jeturing',
    'website': 'https://jeturing.com',
    'license': 'LGPL-3',
    'depends': [
        'web',
        'website',
        'http_routing',
    ],
    'data': [
        'views/branding_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'jeturing_branding/static/src/js/branding_patch.js',
        ],
        'web.assets_frontend': [
            'jeturing_branding/static/src/js/branding_patch.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
