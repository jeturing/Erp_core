# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, tools

from odoo.http import request

HIDEGLOBAL_HELP = _("If checked, the menu will be invisible to all users globally")
HIDDENUSERS_HELP = _("Define users to whom the menu will not be shown. Take into account that the menu will be \
hidden for a user even if this user is defined in 'Show only for users'")
HIDDENUSERS_HELP_PERSONAL = _("This setting defines the menus that users by themselves chose as hidden in the \
preferecenes (shown if a user has an access 'Others > Hide Menus Through Preferences')")
SHOWUSERS_HELP = _("Define users to whom the menu will be specifically shown. If defined, for other users, the menu \
will be hidden. Take into account that the menu might be anyway hidden for chosen users if other settings (e.g. 'Hide \
for users') assume that")
HIDECOMPANIES_HELP = _("Define companies to which the menu will be invisible. Take into account that if a user \
has any available company out of this list, the menu will be shown. Take into account that the menu will be \
hidden for a company even if this company is defined in 'Show only for companies'")
SHOWCOMPANIES_HELP = _("Define companies to which the menu will be specifically shown. If defined, for other \
companies, the menu will be hidden. Take into account that the menu might be anyway hidden for chosen companies if it \
is assumed by the setting 'Hide for companies'")
SHOWGROUPS_HELP = _("Define user groups to whom the menu should be shown. If defined, no other groups will be able \
to access this menu. Take into account that the menu might be anyway hidden if it is assumed by other settings (e.g. \
'Hide for companies' or 'Hide for users')")


def CachedOMM(method):
    """
    The decorator used to check whether companies have been changed, and if yes, to clear ir.ui.menu cache
    In this way, load_menus and get_omm_current_companies would be cleared on any company change (including new tab
    open). So, menus would be recalculated
    """
    def wrapper(self, debug=None):
        """
        The wrapper method itself that is designed for load_menus

        Methods:
         * get_omm_current_companies
         * _get_omm_current_companies
         * clear_cache
        """
        if self._get_omm_current_companies() != self.get_omm_current_companies():
            self.env.registry.clear_cache()
        if debug is None:
            return method(self)
        else:
            return method(self, debug)
    return wrapper


class ir_ui_menu(models.Model):
    """
    Overwrite to add the features to block meny by companies

    Improtant note:
     * writing directly in ir.ui.menu would clear its cache. However, when writing in m2m peer would not trigger
       write of ir.ui.menu (e.g. updating hidden menus in preferences)
       For all other operations, it is necessary to trigger manual ir.ui.menu cache clearing
    """
    _inherit = "ir.ui.menu"

    @api.depends("hide_user_global_ids", "hide_user_ids")
    def _compute_hide_full_user_ids(self):
        """
        Compute method for hide_full_user_ids
        """
        for menu in self:
            hide_full_user_ids = menu.hide_user_global_ids | menu.hide_user_ids
            menu.hide_full_user_ids = [(6, 0, hide_full_user_ids.ids)]

    hide_global = fields.Boolean(string="Hide for everyone", help=HIDEGLOBAL_HELP)
    hide_full_user_ids = fields.Many2many(
        "res.users",
        "ir_ui_menu_res_users_full_rel_table",
        "res_users_id",
        "ir_ui_menu_id",
        string="Hide for users",
        compute=_compute_hide_full_user_ids,
        compute_sudo=True,
        store=True,
    )
    hide_user_global_ids = fields.Many2many(
        "res.users",
        "ir_ui_menu_res_users_global_rel_table",
        "res_users_id",
        "ir_ui_menu_id",
        string="Hide for users (global)",
        help=HIDDENUSERS_HELP,
    )
    hide_user_ids = fields.Many2many(
        "res.users",
        "ir_ui_menu_res_users_omm_rel_table",
        "res_users_id",
        "ir_ui_menu_id",
        string="Hide for users (personal)",
        help=HIDDENUSERS_HELP_PERSONAL,
    )
    show_user_ids = fields.Many2many(
        "res.users",
        "ir_ui_menu_res_users_omm_show_rel_table",
        "res_users_id",
        "ir_ui_menu_id",
        string="Show only for users",
        help=SHOWUSERS_HELP,
    )
    hide_for_company_ids = fields.Many2many(
        "res.company",
        "res_company_ir_ui_menu_omm_hide_rel_table",
        "res_company",
        "ir_ui_menu_id",
        string="Hide for companies",
        help=HIDECOMPANIES_HELP,
    )
    show_for_company_ids = fields.Many2many(
        "res.company",
        "res_company_ir_ui_menu_omm_rel_table",
        "res_company",
        "ir_ui_menu_id",
        string="Show only for companies",
        help=SHOWCOMPANIES_HELP,
    )
    show_for_group_ids = fields.Many2many(
        "res.groups",
        "ir_ui_menu_res_group_show_rel_table",
        "res_groups_id",
        "ir_ui_menu_id",
        string="Show only for groups",
        help=SHOWGROUPS_HELP,
    )

    @api.model
    @api.returns("self")
    def get_user_roots(self):
        """
        Fully re-write to filter also the parent menus

        Methods:
         * get_omm_blacklisted_menus

        Extra info:
         * get_omm_blacklisted_menus - cached method, so here this should influence performance much
        """
        return self.search([("parent_id", "=", False), ("id", "not in", self.get_omm_blacklisted_menus())])

    @api.model
    @CachedOMM
    @tools.ormcache_context("self._uid", "debug", keys=("lang",))
    def load_menus(self, debug):
        """
        Re-write specifically to add the decorator to clear cache
        """
        return super(ir_ui_menu, self).load_menus(debug=debug)

    @api.model
    @CachedOMM
    @tools.ormcache_context("self._uid", keys=("lang",))
    def load_menus_root(self):
        """
        Re-write specifically to add the decorator to clear cache
        """
        return super(ir_ui_menu, self).load_menus_root()

    def _load_menus_blacklist(self):
        """
        Re-write to block menus assumed by hidden menus

        Methods:
         * get_omm_blacklisted_menus

        Extra info:
         * get_omm_blacklisted_menus - cached method, so here this should influence performance much
        """
        res = super()._load_menus_blacklist()
        not_shown_menus = self.get_omm_blacklisted_menus()
        return res + not_shown_menus

    @tools.ormcache("self._uid")
    def get_omm_current_companies(self):
        """
        The method to calculate available companies
        IMPORTANT: This method assumes saving companies to registry CACHE.
        Thus, get_omm_current_companies and get_omm_current_companies might result in different string

        Methods:
         * _get_omm_current_companies

        Returns:
         * str
        """
        return self._get_omm_current_companies()

    @tools.ormcache("frozenset(self.env.user.groups_id.ids)")
    def get_omm_blacklisted_menus(self):
        """
        The method to calculate available companies
        IMPORTANT: This method assumes saving companies to registry CACHE.
        Thus, _get_omm_blacklisted_menus and get_omm_blacklisted_menus might result in different string

        Methods:
         * _get_omm_blacklisted_menus

        Returns:
         * list of ints
        """
        return self._get_omm_blacklisted_menus()

    def _get_omm_current_companies(self):
        """
        The method to calculate available companies

        Returns:
         * str
        """
        return request.httprequest.cookies.get("cids", str(self.env.user.company_id.id))

    def _get_omm_blacklisted_menus(self):
        """
        The method to caclulate menus that should be hidden for that user

        Methods:
         * get_omm_current_companies

        Returns:
          * list of ints - of IDs of ir.ui.menu that should not be shown

        Extra info:
         * Because of groups and companies multi, constructing domain and search requires more resources than get all
           (there is a limited number of menus) and filter those
           Besides, the method is triggerd only after cleared cache
        """
        blacklist_menus = []
        allowed_companies = self.get_omm_current_companies()
        allowed_company_ids = self.env["res.company"].browse([int(cid) for cid in allowed_companies.split(",")])
        current_user = self.env.user
        this_user_group_ids = current_user.groups_id
        context = {"ir.ui.menu.full_list": True, "active_test": False}
        all_menu_ids = self.with_context(context).sudo().search([])
        for menu in all_menu_ids:
            # hidden globally > add to blacklist
            if menu.hide_global:
                blacklist_menus.append(menu.id)
                continue
            # hidden for the current user > add to blacklist
            if menu.hide_full_user_ids and menu.hide_full_user_ids & current_user:
                blacklist_menus.append(menu.id)
                continue
            # shown only for users and the current user is not among those > add to backlist
            if menu.show_user_ids and not (menu.show_user_ids & current_user):
                blacklist_menus.append(menu.id)
                continue
            # hidden for companies and there is * no available company * outside those > add to blacklist
            if menu.hide_for_company_ids:
                if allowed_company_ids & menu.hide_for_company_ids == allowed_company_ids:
                    blacklist_menus.append(menu.id)
                    continue
            # shown only for companys and there is no ANY available companies inside > add to blacklist
            if menu.show_for_company_ids:
                if not (allowed_company_ids & menu.show_for_company_ids):
                    blacklist_menus.append(menu.id)
                    continue
            # show only for groups and user does not have any of those groups > add to blacklist
            if menu.show_for_group_ids:
                if not (this_user_group_ids & menu.show_for_group_ids):
                    blacklist_menus.append(menu.id)
                    continue
        return blacklist_menus

    @api.model
    def action_get_helps(self):
        """
        The method to get ir.ui.menu hierarchy

        Args:
        * target_domain - list - RPR domain to search menus

        Methods:
         * _get_omm_menus_recursively

        Returns:
         * list of strings
        """
        return [
            (HIDEGLOBAL_HELP), _(HIDDENUSERS_HELP), _(SHOWUSERS_HELP), _(HIDECOMPANIES_HELP), _(SHOWCOMPANIES_HELP),
            _(SHOWGROUPS_HELP),
        ]

    @api.model
    def action_get_menu_hierarchy(self, target_domain):
        """
        The method to get ir.ui.menu hierarchy

        Args:
        * target_domain - list - RPR domain to search menus

        Methods:
         * _get_omm_menus_recursively

        Returns:
         * list of dicts (@see action_get_omm_menu_dict)
        """
        context = self._context.copy()
        context.update({"ir.ui.menu.full_list": True})
        viable_only = None
        if target_domain:
            viable_only = self.with_context(context).search(target_domain) or False
            if not viable_only:
                return []
        parent_only_menus = self.with_context(context).search([("parent_id", "=", False)])
        menus = []
        for menu in parent_only_menus:
            menus += menu._get_omm_menus_recursively(viable_only)
        return menus

    def action_get_omm_menu_dict(self):
        """
        The method to prepare menu dict based on menu object

        Returns:
         * dict
          ** id - int
          ** name - char
          ** level - int (for padding)

        Extra info:
         * Expected singleton
        """
        return {
            "id": self.id,
            "name": self.name,
            "web_icon_data": self.web_icon_data,
            "level": self.parent_path.count("/") * 24,
            "hide_global": self.hide_global,
            "hide_user_global_ids": self.hide_user_global_ids.mapped("display_name"),
            "hide_user_ids": self.hide_user_ids.mapped("display_name"),
            "show_user_ids": self.show_user_ids.mapped("display_name"),
            "hide_for_company_ids": self.hide_for_company_ids.mapped("display_name"),
            "show_for_company_ids": self.show_for_company_ids.mapped("display_name"),
            "show_for_group_ids": self.show_for_group_ids.mapped("display_name"),
        }

    def action_get_complete_name(self):
        """
        The method to return complete name

        Returns:
         * str

        Extra info:
         * Expected singleton
        """
        return self.complete_name

    def action_toggle_hide_global(self):
        """
        The method to change the hide_global property

        Returns:
         * bool

        Extra info:
         * Expexted singleton
        """
        new_value = not self.hide_global
        self.write({"hide_global": new_value})
        return new_value

    def _get_omm_menus_recursively(self, viable_only):
        """
        The method to prepare the list of menus dicts

        Args:
         * viable_only - ir.ui.menu recordset or False if no restriction

        Methods:
         * action_get_omm_menu_dict
         * _get_omm_menus_recursively (recursion)

        Returns:
         * list of dicts

        Extra info:
         * Expected singleton
        """
        result = []
        if not viable_only or self in viable_only:
            result.append(self.action_get_omm_menu_dict())
        for child in self.child_id:
            result += child._get_omm_menus_recursively(viable_only)
        return result
