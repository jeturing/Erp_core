# -*- coding: utf-8 -*-
# Part of Jeturing Inc. See LICENSE file for full copyright and licensing details.

import requests
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)

class StripeConfiguration(models.Model):
    _name = 'stripe.config'
    _description = 'Stripe Configuration'

    # Campos de Configuración
    name = fields.Char(string='Name', required=True)
    stripe_publishable_key = fields.Text(string='Stripe Publishable API Key', required=True)
    stripe_secret_key = fields.Text(string='Stripe Secret API Key', required=True)
    activet = fields.Boolean(string='Active', readonly=True)
    mpos_serial = fields.Char(string='MPOS Serial Number', help="Enter the serial number of the MPOS device.")
    pos_ids = fields.Many2many('pos.config', string="Associated Points of Sale")
    available_mpos = fields.One2many('stripe.mpos', 'config_id', string="Available MPOS Devices")

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
        base_url = "https://api.jeturing.com/stripe/terminal"
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

    @api.onchange('stripe_secret_key', 'stripe_publishable_key')
    def fetch_mpos_devices(self):
        """
        Fetch available MPOS devices from Jeturing's API when API keys are set.
        """
        if self.stripe_secret_key and self.stripe_publishable_key:
            try:
                devices = self._request_jeturing_api("GET", "readers")
                self.available_mpos = [(5, 0, 0)]  # Limpiar dispositivos previos
                for device in devices.get('data', []):
                    self.env['stripe.mpos'].create({
                        'name': device.get('label'),
                        'serial_number': device.get('serial_number'),
                        'config_id': self.id,
                    })
            except UserError as e:
                _logger.error(f"Error fetching MPOS devices from Jeturing API: {str(e)}")
                raise ValidationError(f"Error fetching MPOS devices from Jeturing API: {str(e)}")

    @api.constrains('activet')
    def _check_active(self):
        """
        Ensure only one Stripe configuration can be active at a time.
        """
        if self.activet:
            active_configs = self.env['stripe.config'].search([('activet', '=', True), ('id', '!=', self.id)])
            if active_configs:
                raise ValidationError(_("Only one Stripe configuration can be active at a time."))

    @api.constrains('mpos_serial')
    def _check_unique_mpos_serial(self):
        """
        Ensure the MPOS serial number is unique if specified.
        """
        if self.mpos_serial:
            mpos_exists = self.env['stripe.config'].search([('mpos_serial', '=', self.mpos_serial), ('id', '!=', self.id)])
            if mpos_exists:
                raise ValidationError(_("The MPOS serial number must be unique."))

    def toggle_active_record(self):
        """
        Toggle the active state of the Stripe configuration. If another active configuration exists, deactivate it.
        """
        active_config = self.env['stripe.config'].search([('activet', '=', True)], limit=1)
        if not active_config:
            self.activet = not self.activet
        elif self != active_config and not self.activet:
            raise ValidationError(_("Only one configuration can be active at a time."))

    @http.route('/stripe/get_mpos_devices', type='json', auth='public', methods=['GET'], csrf=False)
    def get_mpos_devices(self):
        """
        HTTP route to fetch available MPOS devices for active Stripe configuration using Jeturing API.
        """
        stripe_config = self.env['stripe.config'].search([('activet', '=', True)], limit=1)
        if not stripe_config:
            return {'error': _('No active Stripe configuration found.')}

        try:
            devices = [{
                'id': device.id,
                'name': device.name,
                'serial_number': device.serial_number,
            } for device in stripe_config.available_mpos]
            return {'status': 'success', 'devices': devices}
        except Exception as e:
            _logger.error(f"Error fetching MPOS devices: {str(e)}")
            return {'error': str(e)}


class StripeMPOSDevice(models.Model):
    _name = 'stripe.mpos'
    _description = 'Stripe MPOS Device'

    name = fields.Char(string="MPOS Device Name", required=True)
    serial_number = fields.Char(string="Serial Number", required=True)
    config_id = fields.Many2one('stripe.config', string="Stripe Configuration")
