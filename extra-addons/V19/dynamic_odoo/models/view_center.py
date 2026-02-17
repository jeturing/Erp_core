import string
import random
from lxml import etree
from odoo import models, api, fields
from datetime import datetime


class ActionsCenter(models.Model):
    _name = "ir.actions.center"

    action_id = fields.Many2one(string="Action", comodel_name="ir.actions.act_window")
    views_order = fields.Char(string="Views Order", default='[]')
    name = fields.Char(string="Name")

    @api.model
    def store_action(self, values):
        action_id = values.pop("action_id", False)
        action_virtual = self.search([('action_id', '=', action_id)], limit=1)
        if not action_virtual:
            action_virtual = self.create({'action_id': action_id})
        return action_virtual.write(values)


class ViewCenter(models.Model):
    _name = "studio.view.center"

    arch = fields.Text(string="Arch")
    # store with option 1
    action_id = fields.Many2one(string="Action", comodel_name="ir.actions.act_window")
    view_id = fields.Many2one(string="View id", comodel_name="ir.ui.view")
    # store with option 2
    menu_id = fields.Many2one(string="Menu Id", comodel_name="ir.ui.menu")
    res_model = fields.Char(string="Model Name")
    view_type = fields.Selection([('tree', 'Tree'), ('form', 'Form'), ('kanban', 'Kanban'),
                                  ('search', 'Search'), ('pivot', 'Pivot'), ('dashboard', 'Dashboard'),
                                  ('calendar', 'Calendar'), ('graph', 'Graph')], ondelete='cascade', string="View Type")
    # use for one2many field
    view_key = fields.Char(string="View Key")  # sale_order_field_order_line_list_field_invoice_lines_list
    parent_id = fields.Many2one(string="Parent Id", comodel_name="studio.view.center")

    undo = fields.Many2one(string="Undo", comodel_name="studio.view.center")
    redo = fields.Many2one(string="Redo", comodel_name="studio.view.center")
    is_current = fields.Boolean(string="Is Current")

    new_fields = fields.Many2many('ir.model.fields', string="New Fields", copy=False)

    is_subview = fields.Boolean(string="Is Subview")

    # views_order = fields.Char(string="Views Order", default="[]")  # ["form", "list"]
    # parent_view_key = fields.Char(string="Parent View Key")

    @api.model
    def create_m2o_from_o2m(self, new_field):
        field_m2one = new_field.get('fieldM2one', {})
        model_m2one = self.env['ir.model'].search([('model', '=', field_m2one.get("model_name", False))])
        field_m2one.update({'model_id': model_m2one.id, 'state': 'manual'})
        del field_m2one['model_name']
        self.env['ir.model.fields'].create(field_m2one)
        del new_field['fieldM2one']

    @api.model
    def create_btn_compute(self, raw_field, field, view_store_data):
        model, field_name = raw_field.get("model", False), raw_field.get("name", False),
        relation_field, action_name = raw_field.get("relation_field", False), raw_field.get("action_name", False)
        field[
            'compute'] = "results =self.env['{model}'].read_group(" \
                         "[('{relation_field}', 'in', self.ids)],['{relation_field}'], ['{relation_field}']) \n" \
                         "dic = {{}} \n" \
                         "for x in results: dic[x['{relation_field}'][0]] = x['{relation_field}_count'] \n" \
                         "for record in self: record['{field_name}'] = dic.get(record.id, 0)".format(
            relation_field=relation_field, field_name=field_name, model=model)
        action_data = {'xml_id': action_name, 'name': 'Demo', 'type': 'ir.actions.act_window', 'res_model': model,
                       'view_mode': 'tree,form',
                       'context': "{{'search_default_{field_name}': active_id, 'default_{field_name}': active_id}}".format(
                           field_name=relation_field)}
        action = self.env['ir.actions.act_window'].create(action_data)
        view_store_data['arch'] = view_store_data['arch'].replace(action_name, str(action.id))

    @api.model
    def prepare_new_fields(self, new_fields, model_id, view_store_data):
        field_datas = []
        field_model = self.env['ir.model.fields']
        for new_field in new_fields:
            field = {'ttype': new_field['type'], 'name': new_field['name'], 'related': new_field.get('related', False),
                     'field_description': new_field['string'], 'state': 'manual', 'model_id': model_id}
            field_type = field['ttype']
            if field_type in ["many2one", "many2many", "one2many"]:
                field['relation'] = new_field['relation']
            if field_type == "one2many":
                field['relation_field'] = new_field['relation_field']
            if field_type == "selection":
                field['selection_ids'] = [(0, 0, {'name': option[1], 'value': option[0]}) for option in
                                          new_field['selection']]
            if field_type == "monetary":
                field['currency_field'] = new_field.get('currency_field', False)
                if not field['currency_field']:
                    currency_field = field_model.search(
                        [('model_id', '=', model_id), ('relation', '=', 'res.currency')], limit=1)
                    field['currency_field'] = currency_field.name
                if not field['currency_field']:
                    # create a currency field for monetary field
                    currency_field = 'x_field_%s' % ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))
                    field_datas.append(
                        (0, 0, {'ttype': 'many2one', 'name': currency_field, 'relation': 'res.currency',
                                'field_description': 'Currency for Monetary field', 'state': 'manual',
                                'model_id': model_id}))
                    field['currency_field'] = currency_field
            if new_field.get('compute', False):
                self.create_btn_compute(new_field, field, view_store_data)
            field_datas.append((0, 0, field))

        return field_datas

    @api.model
    def update_field(self, fields_update, model_id):
        field_model = self.env['ir.model.fields']
        for fieldName in fields_update.keys():
            field = field_model.search([('name', '=', fieldName), ('model_id', '=', model_id)], limit=1)
            if len(field):
                field.write(fields_update[fieldName])

    @api.model
    def create_button_data(self, buttons, model_id):
        button_model = self.env['studio.button']
        for button in buttons:
            button_id = button.pop("id")
            button['model_id'] = model_id
            if button_id:
                button_model.browse(button_id).write(button)
            else:
                button_model.create(button)

    @api.model
    def create_approval(self, approvals, model_id):
        button_model = self.env['studio.button']
        rules_model = self.env['studio.approval.rules']
        for button_key in approvals.keys():
            button_data = approvals[button_key]
            approval_group = button_data['rules']
            button = button_model.search([('btn_key', '=', button_key)])
            # check exist button and create if it does not exist
            if not len(button):
                button = button_model.create(
                    {'btn_key': button_key, 'btn_string': button_data['btn_string'], 'model_id': model_id})
            # structure of approval_group {update: [], new: [], delete: []}
            for group_name in approval_group.keys():
                approval_datas = approval_group[group_name]
                for approval in approval_datas:
                    rule_id = approval.pop("id", False)
                    if group_name == "new":
                        approval['btn_id'] = button.id
                        approval['users_to_notify'] = [(4, x) for x in approval.get('users_to_notify', [])]
                        rules_model.create(approval)
                    if rule_id:
                        if group_name == "update":
                            rules_model.browse(rule_id).write(approval)
                        elif group_name == "delete":
                            rules_model.browse(rule_id).unlink()

    @api.model
    def set_default_value(self, default_values):
        default_model = self.env['ir.default']
        field_model = self.env['ir.model.fields']
        for field_name in default_values.keys():
            default_value = default_values[field_name]
            field = field_model.search([['name', '=', field_name]], limit=1)
            if len(field):
                default_exist = default_model.search([['field_id', '=', field.id]])
                if len(default_exist):
                    default_exist.write({'json_value': default_value})
                else:
                    default_model.create({'field_id': field.id, 'json_value': default_value})

    @api.model
    def undo_redo_views(self, view_key, kind):
        last_modifier = self.search([('view_key', '=', view_key), ('is_current', '=', True)], order="id desc", limit=1)
        if kind == "undo":
            last_modifier.write({'is_current': False})
            if not last_modifier.undo:
                return self.reset_view(view_key)
            last_modifier.undo.write({'is_current': True})
        elif last_modifier.redo:
            last_modifier.write({'is_current': False})
            last_modifier.redo.write({'is_current': True})

    @api.model
    def save_with_undo_redo(self, values, view_key):
        old_current = self.search([('view_key', '=', view_key), ('is_current', '=', True)], limit=1)
        if old_current.arch == values.get("arch"):
            return False
        # remove all redo of current
        self.search([['view_key', '=', view_key], ['id', '>', old_current.id]]).unlink()
        # max size history : 3 times
        all_modifier = self.search([['view_key', '=', view_key]], order="id ASC")
        if len(all_modifier) >= 3:
            all_modifier[0].unlink()
        # create new store
        values['undo'] = old_current.id
        new_current = self.create(values)
        old_current.write({'redo': new_current.id, 'is_current': False})
        return new_current

    # @api.model
    # def update_cards(self, cards):
    #     card_model = self.env['view.dashboard']
    #     new_cards, update_cards, delete_cards = cards.get("new", {}), cards.get("update", {}), cards.get("delete", {})
    #     if len(new_cards.keys()):
    #         card_model.search([('key', 'in', list(new_cards.keys()))]).write({'is_draft': False})
    #     if len(update_cards.keys()):
    #         card_model.browse(update_cards.keys()).write({'is_draft': False})
    #         card_model.update_view(update_cards.values())
    #     if len(delete_cards.keys()):
    #         card_model.browse(delete_cards.keys()).unlink()

    @api.model
    def _store_view(self, data):
        def get_data(name):
            return data.get(name, False)

        # card_datas = get_data("card_datas")
        arch, action_id, view_key = get_data("arch"), get_data("action_id"), get_data("view_key")
        menu_id, res_model, view_type = get_data("menu_id"), get_data("res_model"), get_data("view_type")
        new_fields, button_store = get_data("new_fields"), get_data("button_store")
        approvals, default_store = get_data("approvals"), get_data("default_store")
        update_fields, is_subview, view_id = get_data("update_fields"), get_data("is_subview"), get_data("view_id")
        values = {'arch': arch, 'action_id': action_id, 'menu_id': menu_id, 'res_model': res_model,
                  'view_type': view_type, 'is_subview': is_subview, 'view_key': view_key, 'is_current': True,
                  'view_id': view_id}
        model_id = self.env['ir.model'].search([('model', '=', res_model)], limit=1)[0].id
        if button_store:
            self.create_button_data(button_store, model_id)
        if approvals:
            self.create_approval(approvals, model_id)
        # if card_datas:
        #     self.update_cards(card_datas)
        if new_fields:
            values['new_fields'] = self.prepare_new_fields(new_fields, model_id, values)
        if update_fields:
            self.update_field(update_fields, model_id)
        if default_store:
            self.set_default_value(default_store)
        if get_data("STORE"):
            return self.save_with_undo_redo(values, view_key)
        elif new_fields:
            model_fields = self.env['ir.model.fields']
            for field in values['new_fields']:
                model_fields.create(field[2])

    @api.model
    def store_view(self, datas):
        for data in datas:
            self._store_view(data)

    @api.model
    def reset_view(self, view_key):
        self.clear_caches()
        return self.search([('view_key', '=', view_key)]).unlink()
