# -*- coding: utf-8 -*-
import requests
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)

class PaymentTransactions(models.Model):
    _name = 'pos.payment.transaction'
    _description = 'Payment Transaction'
    _rec_name = 'order_name'

    # Campos
    name_on_card = fields.Char(string='Cardholder Name')
    last_4_digits = fields.Char(string="Last 4 Digits of Card", size=4, help="Últimos 4 dígitos de la tarjeta")
    paid_amount = fields.Float(string='Paid Amount', help="Monto pagado en la transacción")
    order_name = fields.Char(string='Order Name')
    mobile = fields.Char(string='Mobile Number')
    transaction_id = fields.Char(string='Transaction ID')
    partner_id = fields.Many2one('res.partner', string='Customer Name')
    cashier_id = fields.Many2one('res.users', string="Cashier", help="Cajero que procesó el pago")
    payment_date = fields.Datetime(string="Payment Date", default=fields.Datetime.now, help="Fecha y hora en que se procesó el pago")
    mpos_serial = fields.Char(string="MPOS Serial Number", help="Número de serie del dispositivo MPOS utilizado")
    state = fields.Selection([
        ('draft', 'New'),
        ('pending', 'Pending'),
        ('fail', 'Failed'),
        ('done', 'Done')
    ], readonly=True, default='draft', copy=False, string="Status")
    
    # Campo para propina
    tips = fields.Float(string='Tip Amount', help="Monto de propina añadido a la transacción")

    @api.model
    def _get_api_key(self) -> str:
        """Obtiene la clave de API desde la configuración de Odoo."""
        api_key = config.get('jeturing_api_key')
        if not api_key:
            error_msg = _("La clave 'jeturing_api_key' no está configurada en el archivo odoo.conf.")
            _logger.error(error_msg)
            raise UserError(error_msg)
        return api_key

    def _get_api_url(self, endpoint: str) -> str:
        """Genera la URL completa para la API de Jeturing."""
        base_url = "http://localhost/stripe/terminal"
        return f"{base_url}/{endpoint}"

    def _request_jeturing_api(self, method: str, endpoint: str, data=None):
        """Realiza una solicitud a la API de Jeturing con manejo de errores detallado."""
        url = self._get_api_url(endpoint)
        headers = {
            "x-api-key": self._get_api_key(),
            "Content-Type": "application/json"
        }
        try:
            response = requests.request(method, url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            error_detail = err.response.json().get("detail", str(err))
            error_msg = _("Error en la API de Jeturing: %s") % error_detail
            _logger.error(f"HTTPError en el endpoint '{endpoint}' con el método '{method}': {error_detail}")
            raise UserError(error_msg)
        except requests.exceptions.RequestException as err:
            _logger.error(_("Error de conexión con la API de Jeturing en '%s': %s") % (url, str(err)))
            raise UserError(_("Error en la conexión con la API de Jeturing"))

    @api.model
    def create_(self, data: dict, order_name: str, amount: float, client_id: int, state: str, last_4_digits: str, cashier_id: int, tips: float = 0.0):
        """
        Método para crear una nueva transacción de pago.

        Args:
            data (dict): Datos de la transacción con el ID de Stripe.
            order_name (str): Nombre de la orden relacionada.
            amount (float): Monto total pagado en la transacción.
            client_id (int): ID del cliente.
            state (str): Estado de la transacción.
            last_4_digits (str): Últimos 4 dígitos de la tarjeta.
            cashier_id (int): ID del cajero.
            tips (float): Monto de propina (opcional).

        Returns:
            obj: Registro de la transacción creada en Odoo.
        """
        if isinstance(data, dict) and 'id' in data:
            vals_list = {
                'transaction_id': data['id'],
                'order_name': order_name,
                'paid_amount': float(amount),
                'state': state,
                'partner_id': client_id,
                'last_4_digits': last_4_digits,
                'cashier_id': cashier_id,
                'payment_date': fields.Datetime.now(),
                'tips': tips  # Almacena la propina en la transacción
            }
            res = super(PaymentTransactions, self).create(vals_list)
            return res
        else:
            error_msg = _("El formato de 'data' no es válido o falta 'id'")
            _logger.error(f"{error_msg}. Valor recibido para 'data': {data}")
            raise UserError(error_msg)

    def get_connection_token(self):
        """Obtiene un token de conexión para el terminal de Stripe desde Jeturing."""
        _logger.info("Solicitando token de conexión para el terminal de Stripe en Jeturing")
        return self._request_jeturing_api("POST", "connection_token")

    def register_reader(self, registration_code: str, label: str, location: str):
        """Registra un nuevo lector en el terminal de Stripe usando la API de Jeturing."""
        _logger.info(f"Registrando nuevo lector en el terminal de Stripe con etiqueta: {label}")
        data = {
            "registration_code": registration_code,
            "label": label,
            "location": location
        }
        return self._request_jeturing_api("POST", "readers", data=data)

    def create_payment_intent(self, amount: int, currency: str, reader_id: str, tips: float = 0.0):
        """Crea un PaymentIntent para el lector de Stripe usando la API de Jeturing.

        Args:
            amount (int): Monto total de la transacción.
            currency (str): Moneda de la transacción.
            reader_id (str): ID del lector en Stripe.
            tips (float): Monto de la propina (opcional).

        Returns:
            dict: Respuesta de la API con el Intento de Pago.
        """
        total_amount = amount + int(tips * 100)  # Convertir la propina y agregar al monto total
        _logger.info(f"Creando PaymentIntent en el terminal de Stripe por el monto total de: {total_amount}")
        data = {
            "amount": total_amount,
            "currency": currency,
            "reader_id": reader_id
        }
        return self._request_jeturing_api("POST", "complete_payment_flow", data=data)
