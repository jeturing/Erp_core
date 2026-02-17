##############################################################################
# Copyright (c) 2022 lumitec GmbH (https://www.lumitec.solutions)
# All Right Reserved
#
# See LICENSE file for full licensing details.
##############################################################################
from odoo import models, fields


class SignTemplate(models.Model):
    _inherit = 'sign.template'

    helpdesk_ticket_template = fields.Boolean(string="Helpdesk Ticket Template", default=False)
