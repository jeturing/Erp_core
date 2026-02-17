import logging

_logger = logging.getLogger(__name__)
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    rule = env.ref('us_messenger.mail_message_record_rule_user') # Rule not seeing mail.message
    name_user = ''
    if rule:
        name_user = rule.name
        rule.unlink()

    rule = env.ref('us_messenger.mail_message_record_rule_admin')  # Rule seeing all mail.message
    name_admin = ''
    if rule:
        name_admin = rule.name
        rule.unlink()

    _logger.info("Deleted %s %s records ir.rule", (name_user,name_admin))
