/** @odoo-module **/
import {NavBar} from "@web/webclient/navbar/navbar";
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";
import {MenuCenter} from "./menu_center";

const {Component} = owl;


class NavBarEdit extends Component {
    setup() {
        this.menuService = useService("menu");
        this.dialog = useService("dialog");
    }

    onShowEdit() {
        // alert("ok")
        this.dialog.add(MenuCenter, {
            // menus: this.menuService.getCurrentApp(),
            // title: "Edit Menu",
            // context: {},
            // resId: false,
            // onRecordSaved: async (record) => {
            // },
        });
    }
}

NavBarEdit.template = "dynamic_odoo.EditMenu";


patch(NavBar.prototype, {
    demo() {
        alert("ok")
    }
    // get currentAppSections() {
    //     return this._super();
    // }
});

NavBar.components = {...NavBar.components, NavBarEdit};
