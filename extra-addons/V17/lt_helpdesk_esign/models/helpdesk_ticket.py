##############################################################################
# Copyright (c) 2022 lumitec GmbH (https://www.lumitec.solutions)
# All Right Reserved
#
# See LICENSE file for full licensing details.
##############################################################################
from odoo import models, fields, api


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    esign_ids = fields.One2many("sign.request", "ticket_id", string="Esign Documents")
    sign_count = fields.Integer("Sign Count", compute="_compute_sign_count", store=True)

    @api.depends('esign_ids')
    def _compute_sign_count(self):
        """Compute sign count"""
        for rec in self:
            doc = self.env['sign.request'].search_count([('ticket_id', '=', rec.id)])
            self.sign_count = doc

    def action_view_document(self):
        return {
            'name': 'Sign Document',
            'view_mode': 'kanban',
            'res_model': "sign.request",
            'domain': [('ticket_id', '=', self.id)],
            'type': 'ir.actions.act_window',
        }

    def send_esign_document(self):
        return {
            'view_mode': 'kanban,tree,form',
            'res_model': "sign.template",
            'domain': [('helpdesk_ticket_template', '=', True)],
            'type': 'ir.actions.act_window',
            'context': {'helpdesk_ticket': True,
                        'partner': self.partner_id.id,
                        'ticket_id': self.id,
                        'assigned_to': self.user_id.partner_id.id
                        }
        }

    def update_esign_count(self):
        for ticket in self.env['helpdesk.ticket'].search([]):
            ticket.sign_count = self.env['sign.request'].search_count([('ticket_id', '=', ticket.id)])
