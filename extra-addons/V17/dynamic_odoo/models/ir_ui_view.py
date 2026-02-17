from lxml import etree
import random
import odoo
from odoo import api, fields, models
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.http import request
from odoo import http


class Model(models.AbstractModel):
    _inherit = 'base'

    def studio_action_button(self):
        def get_context(name):
            return self.env.context.get(name, False)

        btn_key, btn_type, automation_id = get_context("btn_key"), get_context("btn_type"), get_context("automation_id")
        if automation_id:
            automation = self.env['base.automation'].browse(automation_id)
            if len(automation.sudo().action_server_ids) == 1:
                ctx = {
                    'active_model': self._name,
                    'active_ids': self.ids,
                    'active_id': self.id,
                    'domain_post': None,
                }
                return automation.with_context(**ctx).action_server_ids[0].run()
            else:
                automation._process(self)
        elif btn_key:
            button = self.env['studio.button'].search([('btn_key', '=', btn_key)], limit=1)
            if len(button):
                data = {}
                if btn_type == "python":
                    exec(button.python_code)
                    if data.get("action"):
                        return data.get("action")
                elif btn_type == "automation":
                    button.automation_id._process(self)

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super(Model, self).get_view(view_id=view_id, view_type=view_type, **options)

        def get_context(name):
            return self.env.context.get(name, False) or options.get(name)

        action_id = get_context("action") or get_context("action_id")
        if 'studio.view.center' in self.env.registry.models and res:
            view_model = self.env['ir.ui.view']
            domain = [['action_id', '=', action_id], ['res_model', '=', self._name],
                      ['view_type', '=', view_type], ['is_current', '=', True], ['is_subview', '=', False]]
            view_ref = get_context(view_type + "_view_ref")
            if view_ref:
                domain = [['view_key', '=', view_ref.replace("odoo_studio.", "")], ['is_subview', '=', True],
                          ['is_current', '=', True]]
            elif not action_id and not view_ref and res.get("id", False):
                domain.append(['view_id', '=', res['id']])
            # if not action_id:
            #     domain.append(['menu_id', '=', get_context("menu_id")])
            view_center_exist = self.env['studio.view.center'].search(domain, limit=1)
            if len(view_center_exist):
                x_arch, x_models = view_model.with_context(Studio=True).postprocess_and_fields(
                    etree.fromstring(view_center_exist.arch), model=self._name, **options)
                x_models = self._get_view_fields(view_type, x_models)

                for md in x_models.keys():
                    x_models[md] = [x.name for x in self.env['ir.model'].search([('model', '=', md)]).field_id]
                node = etree.fromstring(x_arch)
                node = view_model._postprocess_access_rights(node)

                res['arch'] = etree.tostring(node, encoding="unicode").replace('\t', '')
                res['models'] = x_models
                res['view_studio_id'] = view_center_exist.id
                res['view_key'] = view_center_exist.view_key
                # res['undo'] = view_center_exist.undo
                # res['redo'] = view_center_exist.redo
                res['arch_original'] = x_arch
        return res


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=[('plan', 'Planning'), ('dashboard', 'Dashboard')],
                            ondelete={'plan': 'cascade', 'dashboard': 'cascade'})

    def unlink(self):
        res = super(IrUiView, self).unlink()
        return res

    def read(self, fields=None, load='_classic_read'):
        template_key = self.env.context.get("TEMPLATE_KEY", False)
        res = super(IrUiView, self).read(fields=fields, load=load)

        if len(self) == 1 and self.type == "qweb" and template_key:
            arch = self.get_template_studio(template_key, self.id)
            if arch:
                for view in res:
                    view['arch'] = arch
        return res

    def get_template_studio(self, template_key, view_id):
        template = self.env['studio.template.center'].search(
            [['view_id', '=', view_id], ['is_current', '=', True], ['key', '=', template_key]], limit=1)
        if len(template):
            return template.xml
        return None

    def _get_combined_arch(self):
        return super(IrUiView, self.with_context(VIEW_CHECK=self))._get_combined_arch()

    def _combine(self, hierarchy: dict):
        template_key = self.env.context.get("TEMPLATE_KEY", False)
        view_check = self.env.context.get("VIEW_CHECK", False)
        arch_studio = self.get_template_studio(template_key, view_check.id if view_check else self.id)

        if not arch_studio:
            return super(IrUiView, self)._combine(hierarchy)
        self.ensure_one()
        assert self.mode == 'primary'

        combined_arch = etree.fromstring(arch_studio)
        if self.env.context.get('inherit_branding'):
            combined_arch.attrib.update({
                'data-oe-model': 'ir.ui.view',
                'data-oe-id': str(self.id),
                'data-oe-field': 'arch',
            })
        self._add_validation_flag(combined_arch)
        return combined_arch

    def duplicate_template(self, old_report, new_report):
        new = self.copy()
        cloned_templates, new_key = self.env.context.get('cloned_templates', {}), '%s_cp_%s' % (
            new.key.split("_cp_")[0], random.getrandbits(30))
        self, studio_center = self.with_context(cloned_templates=cloned_templates), self.env['studio.template.center']
        cloned_templates[new.key], arch_tree = new_key, etree.fromstring(self._read_template(self.id))

        for node in arch_tree.findall(".//t[@t-call]"):
            template_call = node.get('t-call')
            if '{' in template_call:
                continue
            if template_call not in cloned_templates:
                template_view = self.search([('key', '=', template_call)], limit=1)
                template_copy = template_view.duplicate_template(old_report, new_report)
                studio_view = studio_center.search([
                    ('view_id', '=', template_view.id), ('key', '=', old_report),
                    ('is_current', '=', True)], limit=1)
                if studio_view:
                    studio_view.copy(
                        {'view_id': template_copy.id, "undo": False, 'redo': False, 'key': new_report})
            node.set('t-call', cloned_templates[template_call])
        subtree = arch_tree.find(".//*[@t-name]")
        if subtree is not None:
            subtree.set('t-name', new_key)
            arch_tree = subtree
        new.write({
            'name': '%s Copy' % new.name,
            'key': new_key,
            'arch_base': etree.tostring(arch_tree, encoding='unicode'),
            'inherit_id': False,
        })
        return new

    @api.model
    def create_new_view(self, values):
        view_mode = values.get('view_mode', False)
        action_id = values.get('action_id', False)
        data = values.get("data", {})
        if view_mode == "list":
            view_mode = "tree"
        view_id = self.create(data)
        values_action_view = {'sequence': 100, 'view_id': view_id.id,
                              'act_window_id': action_id, 'view_mode': view_mode}
        self.env['ir.actions.act_window.view'].create(values_action_view)
        return view_id

    def _render_template(self, template, values=None):
        return super(IrUiView, self.with_context(TEMPLATE_KEY=template))._render_template(template, values=values)

    @api.model
    def render_weblogin(self):
        template = "web.login"
        values = {'databases': http.db_list(), 'response_template': template,
                  'disable_database_manager': not odoo.tools.config['list_db'], 'request': request}
        values.update(AuthSignupHome().get_auth_signup_config())
        if 'website' in self.env.registry.models:
            request.website = self.env['website'].get_current_website()
            request.lang = self.env['res.lang'].browse(getattr(request.website, "_get_cached")('default_lang_id'))
        self.env.registry.clear_cache()
        res = getattr(self.env['ir.ui.view'].with_context(
            {'Studio': True, 'TEMPLATE_KEY': template, 'inherit_branding': False}),
            '_render_template')(template, values)
        return res

    @api.model
    def prepare_view_info(self, arch, model, view_type):
        view_info = {'model': model, 'arch': arch, 'viewType': view_type,
                     'fields': self.env[model].fields_get()}
        options = {}
        x_arch, x_models = self.postprocess_and_fields(
            etree.fromstring(arch), model=model, **options)
        related_models = {}
        for model, model_fields in x_models.items():
            all_fields = [x.name for x in self.env['ir.model'].search([('model', '=', model)]).field_id]
            related_models[model] = self.env[model].fields_get(
                allfields=all_fields, attributes=getattr(self, "_get_view_field_attributes")()
            )
        view_info.update({'arch': x_arch, 'relatedModels': related_models})
        return view_info

    @api.model
    def prepare_views_info(self, views=[]):
        views_info = []
        for view in views:
            view.update(self.prepare_view_info(view.get('arch'), view.get('model'), view.get('viewType')))
            views_info.append(view)
        return views_info
