from odoo import models, api, fields


# class ButtonApproval(models.Model):
#     _name = "studio.approval.button"
#
#     button_key = fields.Char(string="Button Key")
#     model_id = fields.Many2one(comodel_name="ir.model", string="Model")
#     rule_ids = fields.One2many('studio.approval.rules', 'btn_approval_id', string="Rules")
#
#     _sql_constraints = [
#         ('button_key_uniq', 'unique (button_key)', "Button key already exists !"),
#     ]


# class ApprovalRule(models.Model):
#     _name = "studio.approval.rules"
#
#     allowed_group = fields.Many2one(string="Allowed Group", comodel_name="res.groups")
#     responsible = fields.Many2one(string="Responsible", comodel_name="res.users")
#     users_to_notify = fields.Many2one(string="Users to notify", comodel_name="res.users")
#     description = fields.Char(string="Description")
#     exclusive_approval = fields.Boolean(string="Exclusive approval")
#     notification_order = fields.Integer(string="Notification order")
#     btn_approval_id = fields.Many2one(string="Button Approval", comodel_name="studio.approval.button")






