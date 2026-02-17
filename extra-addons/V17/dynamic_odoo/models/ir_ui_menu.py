from odoo import models, api, fields
from lxml import etree
import random


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    model_id = fields.Many2one(string="Model", comodel_name="ir.model")

    def load_web_menus(self, debug):
        web_menus = super(IrUiMenu, self).load_web_menus(debug)
        obj_menus = self.browse(list(filter(lambda x: x != 'root', web_menus.keys())))

        for m in obj_menus:
            if m.id and m.id in web_menus:
                web_menus[m.id]['parent_id'] = [m.parent_id.id, m.parent_id.display_name]
                web_menus[m.id]['sequence'] = m.sequence

        return web_menus

    @api.model
    def create_new_app(self, values):
        app_name, menu_name = values.get("app_name", False), values.get("menu_name", False)
        model_name, web_icon_data = values.get("model_name", False), values.get("app_icon", False)
        # is_new, new_model = values.get("is_new", False), values.get("new_model", False)
        if app_name:
            app_menu = self.create(
                {'name': app_name, 'parent_id': False, 'sequence': 100, 'web_icon_data': web_icon_data})
            menu_root = self.create({'name': menu_name, 'parent_id': app_menu.id, 'sequence': 1})
            values['parent_id'] = menu_root.id
            result = self.create_new_menu(values)
            result['menu_id'] = app_menu.id
            return result
        return False

    @api.model
    def create_new_model(self, model_des, model_name):
        group_no_one = self.env.ref('base.group_no_one').id
        model_values = {'name': model_des, 'model': model_name, 'state': 'manual',
                        'is_mail_thread': True, 'is_mail_activity': True,
                        'access_ids': [(0, 0, {'name': 'Group No One', 'group_id': group_no_one,
                                               "perm_read": True, "perm_write": True, "perm_create": True,
                                               "perm_unlink": True})]}
        return self.env['ir.model'].create(model_values)

    @api.model
    def create_action_wd(self, model_name, is_new):
        name = "New Model"
        if not is_new:
            name = self.env['ir.model'].search([('model', '=', model_name)]).name
        # create action window
        action_window_values = {'name': name, 'res_model': model_name,
                                'view_mode': "tree,form", 'target': 'current', 'view_id': False}
        action_id = self.env['ir.actions.act_window'].create(action_window_values)
        # create tree view
        view_data = {"arch": "<tree><field name='id' /></tree>", "model": model_name,
                     "name": "{model}.tree.{key}".format(model=model_name, key=random.getrandbits(30))}
        view_id = self.env['ir.ui.view'].create_new_view(
            {'view_mode': 'tree', 'action_id': action_id.id, "data": view_data})
        # create form view
        view_data = {
            "arch": "<form>\n"
                    "<header></header>\n"
                    "<sheet>\n"
                    "<div class='oe_button_box' name='button_box'></div><field name='id' invisible='True' />\n"
                    "<div class='ROW row row_title'>\n"
                    "<div class='can_drag col-12'>\n"
                    "<div class='oe_title'>\n"
                    "<h1>\n"
                    "<field name='{name}' is_title='1' required='1' placeholder='Name...'/>\n"
                    "</h1>\n"
                    "</div>\n"
                    "</div>\n"
                    "</div>\n"
                    "</sheet>\n"
                    "</form>".format(name='x_name' if is_new else 'name'),
            "model": model_name,
            "name": "{model}.form.{key}".format(model=model_name, key=random.getrandbits(30))}
        self.env['ir.ui.view'].create_new_view({'view_mode': 'form', 'action_id': action_id.id, "data": view_data})
        self.env['ir.model.data'].create({
            'module': 'odo_studio',
            'name': view_data['name'],
            'model': 'ir.ui.view',
            'res_id': view_id.id,
        })
        return action_id.id

    @api.model
    def create_new_menu(self, values):
        menu_name, sequence = values.get("menu_name", False), values.get("sequence", False)
        model_name = values.get("model_name", False)
        is_new, new_model = values.get("is_new", False), values.get("new_model", False)
        parent_id = values.get("parent_id", False)

        if is_new:
            model_name = self.create_new_model(menu_name, new_model).model
        action_id = self.create_action_wd(model_name, is_new)
        menu = self.create({'name': menu_name, 'parent_id': parent_id, 'sequence': sequence or 1,
                            'action': '%s,%s' % ('ir.actions.act_window', action_id)})
        return {'action_id': action_id, 'menu_id': menu.id}

    @api.model
    def update_menu(self, menus_update):
        for menu in menus_update:
            self.browse(int(menu)).write(menus_update[menu])

    @api.model
    def get_form_view_id(self):
        return self.env.ref('dynamic_odoo.ir_ui_menu_studio_form_view').id


