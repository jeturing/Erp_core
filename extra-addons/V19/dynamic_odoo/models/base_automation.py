from odoo import fields, models, api


class BaseAutomation(models.Model):
    _inherit = "base.automation"

    trigger = fields.Selection(selection_add=[('button_action', 'Button Action')], ondelete={'button_action': 'cascade'})

