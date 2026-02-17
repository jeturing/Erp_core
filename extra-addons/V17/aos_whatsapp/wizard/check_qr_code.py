
import base64
# import functools
import io
import qrcode
from odoo import models, api, _, sql_db, fields
from odoo.exceptions import UserError, ValidationError
import requests
import json
import re
import time
import logging

_logger = logging.getLogger(__name__)


class WaKlikodoo(models.TransientModel):
    _name = "wa.klikodoo.popup"
    _description = "Wa Klikodoo"
    
    whatsapp_server_id = fields.Many2one('ir.whatsapp_server')
    qr_code = fields.Text('QR Code')
    qr_scan = fields.Binary(
        attachment=False, store=True, readonly=True,
        compute='_compute_qrcode',
    )
    whatsapp_number = fields.Char(string="Whatsapp Number")
    status = fields.Selection([('init','Initial Status'),
                               ('loading', 'Loading'),
                               ('got qr code', 'QR Code'),
                               ('authenticated', 'Authenticated')], 
                               compute='_compute_qrcode', string="Status", store=True)
    notes = fields.Text(readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(WaKlikodoo, self).default_get(fields)
        server = self.env[self.env.context.get('active_model')].browse(self.env.context['active_id'])
        if server:
            # KlikApi = server.klikapi()
            # KlikApi.auth()
            res['whatsapp_server_id'] = server.id
            res['whatsapp_number'] = server.whatsapp_number
            if not server.whatsapp_number:
                raise UserError(_('Whatsapp number is required ex: 6281288776713'))
            # payload = {"params": {"method": "status", "client_secret": server.klik_secret}}
            # data_status = KlikApi.get_request(data=payload)
            # print ('===data_status==',data_status.get('accountStatus'))
            # if data_status.get('accountStatus') == 'authenticated':
            #     res['status'] = 'authenticated'
            # elif data_status.get('qrCode'):
            #     res['status'] = 'got qr code'
            # else:
            #     res['status'] = 'loading'
            # print  ('===',res['status'])
            # server.status = res['status']
        return res

    @api.depends('qr_code', 'whatsapp_server_id', 'whatsapp_number')
    def _compute_qrcode(self):
        KlikApi = self.whatsapp_server_id.klikapi()
        # KlikApi.auth()
        for w in self:
            wserver = w.whatsapp_server_id
            payload_up = {
                "params": 
                    {
                        'method': 'update',
                        'client_secret': wserver.klik_secret,
                        'version': self.env['ir.module.module'].sudo().search([('name','=','base')], limit=1).latest_version,
                        'whatsapp_number': wserver.whatsapp_number or '',
                        'whatsapp_webhook': wserver.whatsapp_webhook or '',
                }
            }
            response_up = KlikApi.post_number(data=payload_up)
            # print ('==payload_up=1=',wserver.whatsapp_token,response_up,payload_up)
            payload_qr = {"params": {"client_secret": wserver.klik_secret}}
            data_qr = KlikApi.get_qrcode(data=payload_qr)
            data = io.BytesIO()
            # print ('==_compute_qrcode=2=',data,data_qr,payload_qr)
            if data_qr.get('qrCode'):
                w.status = 'got qr code'
                w.whatsapp_server_id.status = 'got qr code'
                qrcode.make(data_qr.get('qrCode'), box_size=4).save(data, optimise=True, format='PNG')
                w.qr_scan = base64.b64encode(data.getvalue()).decode()
            elif data_qr.get('device_status') == 'connected' and data_qr.get('accountStatus') ==  'authenticated':
                w.status = 'authenticated'
                w.whatsapp_server_id.status = 'authenticated'
            else:
                w.status = 'loading'
                w.whatsapp_server_id.status = 'loading'
                if data_qr.get('message') and data_qr.get('message').get('whatsappStatus') and data_qr.get('message').get('whatsappStatus').get('message'):
                    w.notes = data_qr.get('message').get('whatsappStatus').get('message')

    def klikapi_status(self):
        #WhatsApp is open on another computer or browser. Click “Use Here” to use WhatsApp in this window.
        data = {"params": {"client_id": self.whatsapp_server_id.klik_key, "client_secret": self.whatsapp_server_id.klik_secret}}
        KlikApi = self.whatsapp_server_id.klikapi()
        # KlikApi.auth()
        data_status = KlikApi.get_authenticate(data=data)
        # data_status = KlikApi.get_request(method='status', data=data)
        # print ('===data_status==',data_status)
        # if data_status.get('accountStatus') == 'authenticated':
        #     status = 'authenticated'
        # elif data_status.get('qrCode'):
        #     status = 'got qr code'
        # else:
        #     status = 'loading'
        self.whatsapp_server_id.status = data_status.get('connection')
        self.whatsapp_server_id.whatsapp_token = data_status.get('token')
        return {'type': 'ir.actions.act_window_close'}
