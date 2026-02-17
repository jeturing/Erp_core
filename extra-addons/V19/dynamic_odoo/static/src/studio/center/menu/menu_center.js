/** @odoo-module **/
import {FormViewDialog} from "@web/views/view_dialogs/form_view_dialog";
import {MessageConfirmDialog} from "@mail/core/common/message_confirm_dialog";
import {Dialog} from "@web/core/dialog/dialog";
import {Field} from "@dynamic_odoo/core/fields/field";
import {useService} from "@web/core/utils/hooks";
import {_t} from "@web/core/l10n/translation";

const {Component, useEffect, onWillDestroy, useState} = owl;

class MenuCreator extends Component {

    get data() {
        const data = {};
        Object.keys(this.fields).map((fieldName) => {
            const field = this.fields[fieldName];
            if (field.value) {
                data[fieldName] = field.value;
            }
        });
        delete data[data.is_new ? 'model_name' : 'new_model'];
        return data;
    }

    setup() {
        super.setup();
        // this.onSetup();
        this.fields = this.getFields();
        this.steps = this.getSteps();
        this.state = useState(this.prepareState());
        const onCreate = this.onCreate.bind(this);
        this.env.bus.addEventListener("MENU_CREATOR:CREATE", onCreate);
        onWillDestroy(() => {
            this.env.bus.removeEventListener("MENU_CREATOR:CREATE", onCreate);
        });

    }

    prepareState(step = "create_menu") {
        const views = this.steps[step].views;
        return {step: step, views: views ? views() : [], canNext: this.canNext(step)}
    }

    getFields() {
        return {
            menu_name: {label: "Choose menu name", type: "char"},
            is_new: {
                label: "New model", type: "toggle_switch", value: false, props: {
                    update: (value) => {
                        this.fields.is_new.value = value;
                        this.state.views = this.prepareState(this.state.step).views;
                    }
                }
            },
            model_name: {label: "Choose model", type: "many2one", props: {relation: "ir.model", value_name: "model"}},
            new_model: {
                label: "New model name", type: "char", props: {placeholder: "eg: x_..."}
            },
        }
    }

    getSteps() {
        return {
            // step0: {title: "Welcome to", next: "step1"},
            // step1: {title: "Create your App", next: "step2", prev: "step0", editable: true, views: () => ["app_name"]},
            create_menu: {
                title: "Create your first Menu",
                next: this.onCreate.bind(this),
                // prev: "step1",
                views: () => {
                    const view = ["is_new", "model_name", "menu_name"];
                    if (this.fields.is_new.value) {
                        view.splice(1, 1, "new_model");
                    }
                    return view;
                }
            },
        }
    }

    getProps(field) {
        const fieldProps = {
            label: field.label,
            type: field.type,
            props: {
                update: (value) => {
                    this.fields[field.name].value = value;
                    this.state.canNext = this.canNext();
                }, ...field.props || {}
            }
        }
        if (field.hasOwnProperty("value")) {
            fieldProps.props.value = field.value;
        }
        return fieldProps;
    }

    canNext(step = this.state.step) {
        const views = (this.steps[step].views || (() => ([])))();
        return !views.filter((fieldName) => !this.fields[fieldName].hasOwnProperty('value')).length;
    }

    async onCreate() {
        const {default_values} = this.props;
        const menu = await this.env.services.orm.call("ir.ui.menu", "create_new_menu", [{
            ...this.data, ...(default_values || {}),
        }], {});
        await this.env.bus.trigger("START:RELOAD_MODELS");
        await this.props.reloadMenus(menu.menu_id);
    }


}

MenuCreator.template = "dynamic_odoo.MenuCreator";
MenuCreator.components = {Field};

class MenuCreatorDialog extends Component {
    async onCreate() {
        await this.env.bus.trigger("MENU_CREATOR:CREATE");
        this.props.close();
    }
}

MenuCreatorDialog.template = "dynamic_odoo.MenuCenterDialog";
MenuCreatorDialog.components = {Dialog, MenuCreator};

export class MenuCenter extends Component {
    setup() {
        this.menuService = useService("menu");
        this.dialog = useService("dialog");
        this.state = useState({menus: this.menuService.getCurrentApp()});
        this.menus = this.separateMenus();
        useEffect(() => {
            this.bindDraggable();
            // this.loadEvents();
            // return () => this.removeEvents.bind(this)()
        });
    }

    async newMenu(menuId) {
        let menu = await this.env.services.orm.searchRead("ir.ui.menu", [['id', '=', menuId]], []);
        if (menu.length) {
            menu = menu[0]
            this.dialog.add(MenuCreatorDialog, {
                reloadMenus: this.reloadMenus.bind(this),
                default_values: {parent_id: menu.parent_id[0], sequence: menu.sequence + 1},
            });
        }
    }

    async reloadMenus(menuId = false) {
        await this.env.services.menu.reload();
        this.state.menus = this.menuService.getCurrentApp();
        this.menus = this.separateMenus();
        if (menuId)
            await this.env.services.menu.selectMenu(menuId);
    }

    editMenu(menuId) {
        this.dialog.add(FormViewDialog, {
            title: "Edit Menu",
            context: {},
            resId: menuId,
            resModel: "ir.ui.menu",
            onRecordSaved: async (record) => {
                await this.reloadMenus();
            },
        });
    }

    async deleteMenu(menuId) {
        if (confirm(_t("Do you want to delete this menu ?")) == true) {
            await this.env.services.orm.unlink("ir.ui.menu", [menuId]);
            await this.reloadMenus();
        }
    }

    separateMenus() {
        const menus = {};
        const loop = (menu) => {
            menus[menu.id] = {...menu};
            if (menu.childrenTree.length) {
                menu.childrenTree.map((_menu) => {
                    loop(_menu);
                });
            }
        }
        loop(this.state.menus);
        return menus;
    }

    bindDraggable() {
        const self = this;
        $(".menu_child").sortable({
            connectWith: ".menu_child",
            stop: async function (event, ui) {
                const menusUpdate = {},
                    parentMenuId = parseInt(ui.item.closest(".menu_item[id!='" + ui.item.attr("id") + "']").attr("id"));
                const resetSequence = (el) => {
                    if (!el.length) return;
                    const menu = self.menus[el.attr("id")];
                    const prev = el.prev(), prevMenu = self.menus[prev.attr("id")];
                    if (menu.parent_id[0] != parentMenuId) {
                        menusUpdate[menu.id] = {parent_id: parentMenuId};
                    }
                    if (prevMenu && prevMenu.sequence >= menu.sequence) {
                        menu.sequence = prevMenu.sequence + 1;
                        menusUpdate[menu.id] = {...(menusUpdate[menu.id] || {}), sequence: menu.sequence};
                    }
                    resetSequence(el.next());
                }
                resetSequence(ui.item);
                await self.env.services.orm.call("ir.ui.menu", "update_menu", [menusUpdate], {});
                await self.reloadMenus();
            }
        });
    }
}

MenuCenter.template = "dynamic_odoo.MenuCenter";
MenuCenter.components = {Dialog};