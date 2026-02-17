from odoo import api, fields, models


class IRModelFields(models.Model):
    _inherit = "ir.model.fields"

    @api.model
    def load_related_models(self, model):
        related_models = {}
        record_model = self.env['ir.model'].search([('model', '=', model)])
        field_x_many = record_model.field_id.filtered(lambda x: x.ttype in ['one2many', 'many2many'])
        x_models = [field.relation for field in field_x_many]
        x_models.append(model)
        for model in x_models:
            related_models[model] = self.env[model].fields_get(allfields=[])
        return related_models
