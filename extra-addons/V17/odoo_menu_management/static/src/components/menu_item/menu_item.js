/** @odoo-module **/

import { _lt } from "@web/core/l10n/translation";
import { FormViewDialog } from "@web/views/view_dialogs/form_view_dialog";
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, useState } = owl;


const ommFieldNames = {
    "hide_user_ids": _lt("Hide for users (personal)"),
    "hide_user_global_ids": _lt("Hide for users (global)"),
    "show_user_ids": _lt("Show only for users"),
    "hide_for_company_ids": _lt("Hide for companies"),
    "show_for_company_ids": _lt("Show only for companies"),
    "show_for_group_ids": _lt("Show only for user groups"),
}


export class OMMItem extends Component {
    static template = "odoo_menu_management.OMMItem";
    static props = {
        oMenu:  { type: Object },
        helps: { type: Array },
    };
    /*
    * Re-write to import required services and update props on the component start
    */
    setup() {
        this.state = useState({  oMenu: null });
        this.orm = useService("orm");
        this.dialogService = useService("dialog");
        onWillStart(async () => {
            Object.assign(this.state, { oMenu: this.props.oMenu })
        });
    }
    /*
    * The method to get new menu dict after the update
    */
    async _reloadState(menuId) {
        const newState = await this.orm.call("ir.ui.menu", "action_get_omm_menu_dict", [[menuId]]);
        Object.assign(this.state, { oMenu: newState });
    }
    /*
    * The method to calculate and show a title for the menu header
    */
    async _onShowCompleteName(event, menuId) {
        const menuLine = event.currentTarget;
        if (!menuLine.title) {
            const completeName = await this.orm.call("ir.ui.menu", "action_get_complete_name", [[menuId]]);
            menuLine.title = completeName;
        };
    }
    /*
    * The method to open the full form dialog of the menu
    */
    async _onShowDetails(menuId) {
        var self = this;
        this.dialogService.add(FormViewDialog, {
            resModel: "ir.ui.menu",
            resId: menuId,
            title: _lt("Menu Settings"),
            onRecordSaved: async (formRecord) => { self._reloadState(menuId) },
        });
    }
    /*
    * The method to add/remove hide global
    */
    async _onToggleHideGlobal(event, menuId) {
        const newValue = await this.orm.call("ir.ui.menu", "action_toggle_hide_global", [[menuId]]);
        this._reloadState(menuId)
    }
    /*
    * The method to open the full form dialog of the menu
    */
    async _onOpenM2MChange(menuId, OMMregime) {
        var self = this;
        this.dialogService.add(FormViewDialog, {
            resModel: "ir.ui.menu",
            resId: menuId,
            title: ommFieldNames[OMMregime],
            context: { "form_view_ref": "odoo_menu_management.ir_ui_menu_view_form_omm_m2m", "omm_regime": OMMregime },
            onRecordSaved: async (formRecord) => { self._reloadState(menuId) },
        });
    }
};
