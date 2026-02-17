##############################################################################
# Copyright (c) 2022 lumitec GmbH (https://www.lumitec.solutions)
# All Right Reserved
#
# See LICENSE file for full licensing details.
##############################################################################
from odoo import models, fields, api, Command


class SignRequest(models.Model):
    _inherit = 'sign.request'

    ticket_id = fields.Many2one('helpdesk.ticket', string="Ticket")
