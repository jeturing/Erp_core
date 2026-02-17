from odoo import models, api, fields


class TemplateCenter(models.Model):
    _name = "studio.template.center"

    xml = fields.Text(string="Xml")
    view_id = fields.Many2one(string="View id", comodel_name="ir.ui.view")
    key = fields.Char(string="Template Key")
    is_current = fields.Boolean(string="Is Current Edited")
    undo = fields.Many2one(string="Undo", comodel_name="studio.template.center")
    redo = fields.Many2one(string="Redo", comodel_name="studio.template.center")

    @api.model
    def can_undo_redo(self, template_id):
        studio_template = self.search(
            [('key', '=', template_id), ('is_current', '=', True)], order="id desc", limit=1)
        result = {'can_undo': False, 'can_redo': False}
        if len(studio_template):
            result['can_undo'] = True
            result['can_redo'] = True if studio_template.redo else False
        return result

    @api.model
    def undo_redo_template(self, template_key, kind):
        last_modifier = self.search([['key', '=', template_key], ['is_current', '=', True]],
                                    order="id desc", limit=1)
        if kind == "undo":
            last_modifier.write({'is_current': False})
            if not last_modifier.undo:
                return self.reset_view(template_key)
            self.search([['key', '=', template_key], ['view_id', '=', last_modifier.view_id.id],
                         ['id', '<', last_modifier.id]], order="id desc", limit=1).write({'is_current': True})
        else:
            self.search([['key', '=', template_key],
                         ['view_id', '=', last_modifier.redo.view_id.id]]).write({'is_current': False})
            last_modifier.redo.write({'is_current': True})

    @api.model
    def store_template(self, template_key, template_id, arch_string):
        all_modifier = self.search([['key', '=', template_key], ['view_id', '=', template_id]], order="id ASC")
        # max size history
        if len(all_modifier) >= 10:
            all_modifier[0].unlink()
        all_current = self.search([['key', '=', template_key], ['is_current', '=', True]], order="id DESC")
        last_modifier = all_current[0] if len(all_current) else self
        # remove all view has undo
        for current in all_current:
            self.search([['key', '=', template_key],
                         ['view_id', '=', current.view_id.id], ['id', '>', current.id]]).unlink()
        # get current view of that template
        views_exist = all_current.filtered(lambda x: x.view_id.id == template_id)
        # create new template and set to current
        view_value = {'xml': arch_string, 'view_id': template_id,
                      'undo': last_modifier.id, 'is_current': True, 'key': template_key}
        new_view = self.create(view_value)
        # set redo for last modifier from new view created
        last_modifier.write({'redo': new_view.id})
        if views_exist.id:
            views_exist.write({'is_current': False})
        return new_view

    @api.model
    def reset_view(self, template_key):
        if template_key:
            return self.search([['key', '=', template_key]]).unlink()
        return False
