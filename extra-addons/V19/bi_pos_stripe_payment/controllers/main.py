# -*- coding: utf-8 -*-
import logging
import werkzeug
import json
import stripe
from odoo import http
from odoo.http import request
from odoo.tools.float_utils import float_round

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_stripe import utils as stripe_utils
from odoo.addons.payment_stripe.const import HANDLED_WEBHOOK_EVENTS


_logger = logging.getLogger(__name__)

try:
    import stripe
except ImportError: 
    _logger.debug('Can not import stripe`.')

class StripeController(http.Controller):
	
	
	@http.route('/create-payment-intent', type='json', auth='public', csrf=False)
	def create_payment(self, **kwargs):
		try:
			data = kwargs

			if data.get('stripe_data'):
				for key in data.get('stripe_data'):
					stripe.api_key = key.get('stripe_secret_key')
			intent = stripe.PaymentIntent.create(
				amount=round(float_round(data['amount'] * 100, 2)),
				currency=data['currency'],
				description="Do Payment",
				
			)
			return intent
		except Exception as e:
			error=str(e)
			return error
