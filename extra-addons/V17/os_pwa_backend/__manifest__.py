# Part of Odoo Stars .
{
    "name": "Progressive Web Application (PWA) [Backend]",
    "author": "Odoo Stars ",
    "website": "https://www.odoo-stars.com",
    "support": "support@odoo-stars.com",
    'version': '1.0',
    "category": "Extra Tools",
    "license": "OPL-1",
    "summary": "Backend PWA App , Progressive Web Apps Backend, Odoo PWA, PWA, Progressive Web App for Odoo",
    "description": """
     The PWA (progressive web application) for Odoo Backend is like a mobile application, customizable and complete.
    """,
    "depends": ['base', 'web', 'base_setup'],
    "data": [
        "data/data.xml",
        "security/ir.model.access.csv",
        "views/views.xml",
        "views/pwa_configuration_view.xml",
    ],
    'assets': {
        "web.assets_backend": [
            "/os_pwa_backend/static/src/js/pwa_start.js",
        ]
    },

    'images': ['static/description/main_screenshot.png'],
    "installable": True,
    "auto_install": False,
    "application": True,
    "price": "25",
    'live_test_url': 'https://butterfly.odoo-stars.com/r/5M3',
    "currency": "EUR"
}
