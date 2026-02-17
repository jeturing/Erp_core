# from odoo import models, api, fields
# import random
#
#
# class IrUiMenu(models.Model):
#     _inherit = 'ir.ui.menu'
#
#     model_id = fields.Many2one(string="Model", comodel_name="ir.model")
#
#     def load_web_menus(self, debug):
#         web_menus = super(IrUiMenu, self).load_web_menus(debug)
#         obj_menus = self.browse(list(filter(lambda x: x != 'root', web_menus.keys())))
#
#         for m in obj_menus:
#             if m.id and m.id in web_menus:
#                 web_menus[m.id]['parent_id'] = [m.parent_id.id, m.parent_id.display_name]
#                 web_menus[m.id]['sequence'] = m.sequence
#
#         return web_menus
#
#     @api.model
#     def create_new_app(self, values):
#         app_name, menu_name, model_name, web_icon_data = values.get("app_name", False), values.get("object_name",
#                                                                                                    False), values.get(
#             "model_name", False), values.get("web_icon_data", False)
#         if app_name:
#             app_menu = self.create(
#                 {'name': app_name, 'parent_id': False, 'sequence': 100, 'web_icon_data': web_icon_data})
#             parent_menu = self.create({'name': menu_name, 'parent_id': app_menu.id, 'sequence': 1})
#             values['parent_id'] = parent_menu.id
#             result = self.create_new_menu(values)
#             result['menu_id'] = app_menu.id
#             return result
#         return False
#
#     @api.model
#     def create_new_model(self, model_des, model_name):
#         model_values = {'name': model_des, 'model': model_name, 'state': 'manual',
#                         'is_mail_thread': True, 'is_mail_activity': True,
#                         'access_ids': [(0, 0, {'name': 'Group No One', 'group_id':
#                             self.env.ref('base.group_no_one').id, "perm_read": True, "perm_write": True,
#                                                "perm_create": True, "perm_unlink": True})]}
#         return self.env['ir.model'].create(model_values).id
#
#     @api.model
#     def create_action_wd(self, model_name):
#         # create action window
#         action_window_values = {'name': 'New Model', 'res_model': model_name,
#                                 'view_mode': "tree,form", 'target': 'current', 'view_id': False}
#         action_id = self.env['ir.actions.act_window'].create(action_window_values)
#         # create tree view
#         view_data = {"arch": "<tree><field name='id' /></tree>", "model": model_name,
#                      "name": "{model}.tree.{key}".format(model=model_name, key=random.getrandbits(30))}
#         view_id = self.env['studio.view.center'].create_new_view(
#             {'view_mode': 'tree', 'action_id': action_id.id, "data": view_data})
#         # create form view
#         view_data = {
#             "arch": "<form><header></header><sheet><div class='oe_button_box' name='button_box'></div><field name='id' invisible='True' /></sheet></form>",
#             "model": model_name,
#             "name": "{model}.form.{key}".format(model=model_name, key=random.getrandbits(30))}
#         self.env['studio.view.center'].create_new_view(
#             {'view_mode': 'form', 'action_id': action_id.id, "data": view_data})
#         self.env['ir.model.data'].create({
#             'module': 'odo_studio',
#             'name': view_data['name'],
#             'model': 'ir.ui.view',
#             'res_id': view_id.id,
#         })
#         return action_id.id
#
#     @api.model
#     def create_new_menu(self, values):
#         model_name, model_id, menu_name, empty_view = values.get("model_name", False), values.get("model_id", False), \
#             values.get("object_name", False), values.get("empty_view", False)
#         action_id, parent_id, sequence = False, values.get("parent_id", False), values.get("sequence", False)
#         if model_name:
#             model_id = self.create_new_model(menu_name, model_name)
#             action_id = self.create_action_wd(model_name)
#         else:
#             model_obj = self.env['ir.model'].browse(model_id)
#             if empty_view:
#                 action_id = self.create_action_wd(model_obj.model)
#             else:
#                 action_ids = self.env['ir.actions.act_window'].search([('res_model', '=', model_obj.model)])
#                 if len(action_ids):
#                     has_view = action_ids.filtered(lambda x: x.view_id != False)
#                     if len(has_view):
#                         has_tree = has_view.filtered(lambda x: (x.view_mode or "").find("tree") >= 0)
#                         action_ids = has_tree if len(has_tree) else has_view
#                     action_id = action_ids[0].id
#         # create menu
#         if model_id:
#             menu = self.create({'name': menu_name, 'parent_id': parent_id, 'sequence': sequence or 1,
#                                 'action': '%s,%s' % ('ir.actions.act_window', action_id)})
#             return {'action_id': action_id, 'menu_id': menu.id}
#         return False
#
#     @api.model
#     def update_menu(self, menu_update, menu_delete):
#         self.browse(menu_delete).unlink()
#         for menu in menu_update:
#             self.browse(int(menu)).write(menu_update[menu])
#
#     @api.model
#     def get_form_view_id(self):
#         return self.env.ref('dynamic_odoo.ir_ui_menu_studio_form_view').id
