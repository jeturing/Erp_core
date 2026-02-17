{
    'name': 'Stripe Payment Acquirer for POS',
    'version': '19.0.0.1',
    'category': 'Point of Sale',
    'summary': 'Point of sales stripe payment gateway for pos stripe payment gateway for Stripe Payment Acquirer for pos Stripe gateway for point of sale stripe payment Acquirer for pos stripe payment pay pos order from stripe payment pos order stripe payment for pos',
    'description': """
    
   This odoo app helps user to accept point of sales customer payment though stripe payment getway, user can pay point of sale order payment by stripe payment acquirer.
    
    """,
    'author': 'BrowseInfo',
    'website': 'https://www.browseinfo.com',
    'currency': 'EUR',
    'depends': [
        'base',
        'point_of_sale',
        'pos_stripe',
        'pos_self_order_stripe',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/stripe_config.xml',
        'views/payment_transactions.xml',
    ],
    'external_dependencies': {'python': ['stripe']},
    'assets': {'point_of_sale._assets_pos': ['bi_pos_stripe_payment/static/src/css/stripe_popup.css', 'bi_pos_stripe_payment/static/src/js/model.js', 'bi_pos_stripe_payment/static/src/js/PaymentScreen.js', 'bi_pos_stripe_payment/static/src/js/StripePopup.js', 'bi_pos_stripe_payment/static/src/xml/stripe_payment.xml']},
    'license': 'OPL-1',
    'auto_install': False,
    'installable': True,
    'live_test_url': 'https://youtu.be/2H-fxpCd0Lk',
    'images': [
        'static/description/Banner.gif',
    ],
}
