##############################################################################
# Copyright (c) 2022 lumitec GmbH (https://www.lumitec.solutions)
# All Right Reserved
#
# See LICENSE file for full licensing details.
##############################################################################
from odoo.tests import common
from odoo.tools import file_open


class TestEsign(common.TransactionCase):
    def setUp(self):
        super(TestEsign, self).setUp()

    def test_create_sign_request(self):
        """Creation of sign request from sign template"""
        ticket = self.env['helpdesk.ticket'].create({
            'name': 'Test Ticket',
        })
        partner = self.env['res.partner'].create({
            'name': 'Test Partner 1',
            'email': 'partnertest_1@example.com',
        })
        with file_open('sign/static/demo/sample_contract.pdf', "rb") as f:
            pdf_content = f.read()
        attachment = self.env['ir.attachment'].create({
            'type': 'binary',
            'raw': pdf_content,
            'name': 'test_employee_contract.pdf',
        })
        template = self.env['sign.template'].create({
            'name': 'Sign Template',
            'attachment_id': attachment.id,
        })
        role = self.env['sign.item.role'].create({
            'name': 'Tester',
            'default': False
        })
        template.write({'sign_item_ids': self.env['sign.item'].create([
            {
                'type_id': self.env.ref('sign.sign_item_type_signature').id,
                'required': True,
                'responsible_id': role.id,
                'page': 1,
                'posX': 0.273,
                'posY': 0.158,
                'template_id': template.id,
                'width': 0.150,
                'height': 0.015,
            }
            ])
        })
        employee = self.env['sign.send.request.signer'].create([{
            'role_id': role.id,
            'partner_id': partner.id
        }])
        send_request = self.env['sign.send.request'].create({
            'template_id': template.id,
            'signer_ids': employee,
            'ticket_id': ticket.id,
            'filename': 'Test File',
            'subject': 'Test Subject',
            'signers_count': len(role),
        })
        sign_request_id = send_request.create_request()['id']
        sign_request = self.env['sign.request'].browse(sign_request_id)
        self.assertEqual(1, len(sign_request))
        self.assertEqual(1, ticket.sign_count)
