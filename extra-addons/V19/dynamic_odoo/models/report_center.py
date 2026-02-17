from odoo import models, api, fields
import random


class ReportCenter(models.Model):
    _inherit = "studio.template.center"

    report_id = fields.Many2one(string="Report Id", comodel_name="ir.actions.report")
    is_report = fields.Boolean(string="Is Report")

    @api.model
    def create_new_report(self, values):
        self.env['ir.ui.view']._load_records([dict(xml_id=values.get("xml_id", False), values={
            'name': values.get("name", False),
            'arch': values.get("xml", False),
            'key': values.get("xml_id", False),
            'inherit_id': False,
            'type': 'qweb',
        })])
        model_id = self.env['ir.model'].search([["model", '=', values['model']]]).id
        report = self.env["ir.actions.report"].create({
            'model': values['model'],
            "binding_type": "report",
            "binding_model_id": model_id,
            "model_id": model_id,
            "name": values['string'],
            "report_file": values['report_file'],
            "report_name": values['report_name'],
            "report_type": "qweb-pdf",
            "type": "ir.actions.report",
            "xml_id": values['report_xml_id']
        })
        return {'id': report.id, 'name': report.name, 'report_name': report.report_name}

    @api.model
    def store_template(self, template_key, template_id, arch_string):
        res = super(ReportCenter, self).store_template(template_key, template_id, arch_string)
        if self.env.context.get("IS_REPORT", False):
            res.write({'is_report': True})
        return res

    @api.model
    def get_field_widget(self):
        all_models = self.env.registry.models
        models_name = all_models.keys()
        widgets = {}
        for model_name in models_name:
            if model_name.find("ir.qweb.field.") >= 0:
                widget_name = model_name.replace("ir.qweb.field.", "")
                self.env[model_name].get_available_options()
                widgets[widget_name] = self.env[model_name].get_available_options()
        return widgets
