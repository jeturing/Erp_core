import logging

_logger = logging.getLogger(__name__)
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    print('migrate!')
    env = api.Environment(cr, SUPERUSER_ID, {})
    rule = env.ref('us_messenger.mail_message_record_rule_user', False)  # Rule not seeing mail.message
    if rule:
        rule.unlink()

    rule = env.ref('us_messenger.mail_message_record_rule_admin', False)  # Rule seeing all mail.message
    if rule:
        rule.unlink()
