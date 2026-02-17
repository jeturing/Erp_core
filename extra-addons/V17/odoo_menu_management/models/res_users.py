# -*- coding: utf-8 -*-

from odoo import models, fields


class res_users(models.Model):
    """
    Re write to add activities to-do settings
    """
    _inherit = ["res.users"]

    def _compute_can_see_hidden_menus(self):
        """
        Compute method for can_see_hidden_menus
        This method represents a hack since the attribute "groups" doesn't work correctly on a user preferences form
        """
        can_see_hidden_menus = self.env.user.has_group("odoo_menu_management.group_omm")
        for res_user in self:
            res_user.can_see_hidden_menus = can_see_hidden_menus

    def _inverse_hide_menu_ids(self):
        """
        Re-write to clear ir.ui.menu cache

        Methods:
         * clear_cache
        """
        self.env.registry.clear_cache()

    hide_menu_ids = fields.Many2many(
        "ir.ui.menu",
        "ir_ui_menu_res_users_omm_rel_table",
        "ir_ui_menu_id",
        "res_users_id",
        string="Hide menus",
        inverse=_inverse_hide_menu_ids,
    )
    can_see_hidden_menus = fields.Boolean(string="Can change hidden menus", compute=_compute_can_see_hidden_menus)

    @property
    def SELF_READABLE_FIELDS(self):
        """
        Re-write to allow users to hide menus
        """
        return super().SELF_READABLE_FIELDS + ["hide_menu_ids", "can_see_hidden_menus"]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        """
        Re-write to allow users to hide menus
        """
        return super().SELF_WRITEABLE_FIELDS + ["hide_menu_ids", "can_see_hidden_menus"]
