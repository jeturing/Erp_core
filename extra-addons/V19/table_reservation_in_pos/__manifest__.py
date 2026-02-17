{
    'name': 'Table Reservation in POS',
    'version': '19.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """The Table Reservation in Pos module is used to facilitate
    the management of reservations""",
    'description': 'The Table Reservation in Pos module is a comprehensive solution that combines reservation management with the functionality of a reserve table in POS system.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'AGPL-3',
    'depends': [
        'base',
        'point_of_sale',
        'pos_restaurant',
    ],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'assets': {'point_of_sale._assets_pos': ['table_reservation_in_pos/static/src/xml/*', 'table_reservation_in_pos/static/src/js/*', 'table_reservation_in_pos/static/src/scss/*']},
    'installable': True,
    'auto_install': False,
    'application': False,
}
