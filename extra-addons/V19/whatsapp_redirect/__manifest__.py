{
    'name': 'Send Whatsapp Message Odoo17',
    'version': '19.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Whatspp Web,Whatsapp Odoo Integration, Odoo Whatsapp Connector, Odoo Whatsapp, Whatsapp Connector, Whatsapp Integration, Odoo17, Whatsapp, Odoo Apps',
    'description': 'This module helps you to directly send messages to your contacts through WhatsApp web.',
    'author': 'Cybrosys Techno solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'base',
        'contacts',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'wizard/whatsapp_send_message_views.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
