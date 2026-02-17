from odoo import models, api, fields, _
from datetime import datetime
from markupsafe import Markup
from odoo.exceptions import UserError


class StudioButton(models.Model):
    _name = "studio.button"

    btn_key = fields.Char(string="Button Key")
    btn_string = fields.Char(string="Button String")
    python_code = fields.Text(string="Arch")
    automation_id = fields.Many2one(string="Automation", comodel_name="base.automation")
    model_id = fields.Many2one(string="Model", comodel_name="ir.model")
    rule_ids = fields.One2many('studio.approval.rules', 'btn_id', string="Rules")

    _sql_constraints = [
        ('btn_key_uniq', 'unique (btn_key)', "Button key already exists !"),
    ]


class ApprovalRule(models.Model):
    _name = "studio.approval.rules"

    allowed_group = fields.Many2one(string="Allowed Group", comodel_name="res.groups")
    responsible = fields.Many2one(string="Responsible", comodel_name="res.users")
    users_to_notify = fields.Many2many("res.users", string="Users to notify")
    description = fields.Char(string="Description")
    exclusive_approval = fields.Boolean(string="Exclusive approval")
    notification_order = fields.Integer(string="Notification order")
    btn_id = fields.Many2one(string="Button Approval", comodel_name="studio.button", ondelete='cascade')
    btn_key = fields.Char(string="Button Key", related="btn_id.btn_key")
    filter = fields.Char(string="Filter")


class ApprovalDetails(models.Model):
    _name = "studio.approval.details"

    res_id = fields.Char(string="Record Id")
    model_id = fields.Many2one(comodel_name="ir.model", string="Model")
    rule_id = fields.Many2one(comodel_name="studio.approval.rules", string="Rule", ondelete='cascade')
    notification_order = fields.Integer(string="Notification order", related="rule_id.notification_order", store=True)
    state = fields.Selection(selection=[['wait', 'Wait'], ['accept', 'Accept'], ['decline', 'Decline']],
                             ondelete='cascade', default="wait")
    user_accepted = fields.Many2one(comodel_name="res.users", string="User Accepted")
    date_accepted = fields.Datetime(string="Date Accepted")

    @api.model
    def get_approval(self, model, res_id):
        model = self.env['ir.model'].sudo().search([['model', '=', model]])
        buttons = self.env["studio.button"].search([["model_id", "=", model.id]])
        approval = self.search([["res_id", "=", res_id], ["model_id", "=", model.id]])
        rule_ids, result = [ap.rule_id.id for ap in approval], {}
        for button in buttons:
            for rule in button.rule_ids:
                record = self.env[model.model].search(eval(rule.filter or '[]') + [('id', '=', res_id)])
                if not res_id:
                    if not len(record) and rule.id not in rule_ids:
                        self.create({'res_id': res_id, 'model_id': model.id, 'rule_id': rule.id})
                else:
                    if len(record):
                        if rule.id not in rule_ids:
                            self.create({'res_id': res_id, 'model_id': model.id, 'rule_id': rule.id})
                    elif rule.id in rule_ids:
                        self.search(
                            [('res_id', '=', res_id), ('rule_id', '=', rule.id), ('model_id', '=', model.id)]).unlink()

        for detail in self.search([["res_id", "=", res_id], ["model_id", "=", model.id]],
                                  order="notification_order"):
            btn_key = detail.rule_id.btn_id.btn_key
            if btn_key not in result:
                result[btn_key] = []
            result[btn_key].append({'id': detail.id, 'button': btn_key, 'state': detail.state,
                                    'group_id': detail.rule_id.allowed_group.id,
                                    'group_name': detail.rule_id.allowed_group.full_name,
                                    'description': detail.rule_id.description, 'rule_id': detail.rule_id.id,
                                    'user_accepted': detail.user_accepted.display_name,
                                    'date_accepted': detail.date_accepted, 'user_id': detail.user_accepted.id})
        return result

    def make_message(self):
        thread = self.env[self.model_id.model].browse(int(self.res_id))
        thread.message_post(
            body=Markup("<span><span>%s</span> as <span class='sp2'>%s</span></span>") % (
                {'accept': 'Approved', 'decline': 'Rejected', 'wait': 'Reset Approval'}[self.state],
                self.rule_id.allowed_group.full_name,
            ))
        # if len(self.rule_id.users_to_notify) and self.state == 'accept':
        #     link = '<a href="/web#model=res.partner&amp;id=%d" class="o_mail_redirect" data-oe-id="7" ' \
        #            'data-oe-model="res.partner" target="_blank" contenteditable="false">@%s</a>'
        #     tags = Markup(' '.join([link % (x.id, x.name) for x in self.rule_id.users_to_notify]))
        #     thread.message_post(
        #         body=Markup("%s <br>An approval for '%s (%s)' has been requested on %s") % (
        #             tags, self.rule_id.btn_id.btn_string, self.model_id.name, thread.display_name),
        #         partner_ids=self.rule_id.users_to_notify.ids)

    def request_approval(self):
        thread = self.env[self.model_id.model].browse(int(self.res_id))
        link = '<a href="/web#model=res.partner&amp;id=%d" class="o_mail_redirect" data-oe-id="7" ' \
               'data-oe-model="res.partner" target="_blank" contenteditable="false">@%s</a>'
        tags = Markup(' '.join([link % (x.id, x.name) for x in self.rule_id.users_to_notify]))
        thread.message_post(
            body=Markup("%s <br>An approval for '%s (%s)' has been requested on %s") % (
                tags, self.rule_id.btn_id.btn_string, self.model_id.name, thread.display_name),
            partner_ids=self.rule_id.users_to_notify.ids)

    def do_action(self, values):
        user_id = self.env.user.id
        # check exclusive approval
        rule_ids = self.rule_id.btn_id.rule_ids
        exclusive_rule = self.search([('res_id', '=', self.res_id), ('rule_id', 'in', rule_ids.ids),
                                      ('rule_id.exclusive_approval', '=', True),
                                      ('state', 'in', ['accept', 'decline']), ('user_accepted', '=', user_id)])
        if len(exclusive_rule) and self.id not in exclusive_rule.ids:
            raise UserError(
                _('\nThis approval or the one you already submitted limits you to a single approval on this action. \n'
                  'Another user is required to further approve this action.'))
        responsible = self.rule_id.responsible.ids or self.rule_id.allowed_group.users.ids
        if (user_id in responsible) or len(responsible) == 0:
            values['date_accepted'] = datetime.now()
            if values['state'] in ["accept", "decline"]:
                values['user_accepted'] = user_id
            else:
                values['user_accepted'] = False
            self.write(values)
            notifications, approvals = [], self.sudo().get_approval(self.sudo().model_id.model, self.sudo().res_id)
            for user in self.env.user.search([]):
                notifications.append([user.partner_id, "approval_data",
                                      {'id': user.partner_id.id, 'type': 'approval_data', 'approvals': approvals,
                                       'partner_id': user.partner_id.id}])
            self.env['bus.bus'].sudo()._sendmany(notifications)
            self.make_message()
