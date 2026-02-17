/** @odoo-module **/

import {useService} from "@web/core/utils/hooks";
import {FormViewDialog} from "@web/views/view_dialogs/form_view_dialog";
import AppCenter from "./app/app_center";
import ReportCenter from "./report/report_center";
import ViewCenter from "./views/view_center";
import MoreCenter from "./more/more_center";


const {Component, onMounted, onWillUnmount, useState, useEffect, onWillStart, xml} = owl;

export default class StudioCenter extends Component {
    setup() {
        super.setup();
        this.dialog = useService("dialog");
        this.state = useState({type: "view"});
        useEffect(() => {
            document.getElementsByClassName("o_web_client")[0].setAttribute("type", this.state.type);
        });
        const onReloadMenu = () => {
            this.render(true);
        }
        onMounted(() => {
            this.env.bus.addEventListener("STUDIO:MENUS-CHANGED", onReloadMenu);
        });
        onWillUnmount(() => {
            this.env.bus.removeEventListener("STUDIO:MENUS-CHANGED", onReloadMenu);
        });
    }

    get center() {
        const resModel = odoo.studio.getState().model;
        return {
            view: {
                icon: "fa fa-window-restore",
                save: true,
                reset: true,
                title: "View Center",
                component: ViewCenter,
                props: {resModel: resModel}
            },
            app: {
                icon: "fa fa-adn",
                title: "App Creator Center",
                component: AppCenter,
                props: {onCreate: () => this.state.type = "view"}
            },
            report: {
                icon: "fa fa-newspaper-o",
                reset: true,
                title: "Report Center",
                component: ReportCenter,
                props: {resModel: resModel}
            },
            more: {
                icon: "fa fa-ellipsis-h",
                title: "More Center",
                reset: true,
                component: MoreCenter,
                props: {resModel: resModel}
            },
        }
    }

    onReset() {
        this.env.bus.trigger(`${this.state.type.toUpperCase()}_CENTER:RESET`);
    }

    onSave() {
        this.env.bus.trigger(`${this.state.type.toUpperCase()}_CENTER:SAVE`);
    }

    onNewModel() {
        const self = this;
        this.dialog.add(FormViewDialog, {
            title: "Create New Model",
            context: {},
            resId: false,
            resModel: "ir.model",
            onRecordSaved: async (record) => {
                self.env.bus.trigger("START:RELOAD_MODELS")
            },
        });
    }

    async onCloseCenter() {
        this.env.bus.trigger("CLEAR-CACHES");
        this.env.bus.trigger("VIEW-CENTER:CLOSE");
        const {action, view_type} = odoo.studio.getState();
        const actionService = this.env.services.action;
        if (action) {
            const actionInfo = await actionService.loadAction(action);
            if (["ir.actions.act_window"].includes(actionInfo.type)) {
                await actionService.doAction(action, {
                    clearBreadcrumbs: true,
                    random: Math.random()
                });
                if (view_type != actionService.currentController.view.type) {
                    await actionService.switchView(view_type, {});
                }
            } else {
                await actionService.loadState();
            }
        }
        this.env.bus.trigger("STUDIO:CLOSE");
    }
}

StudioCenter.template = "dynamic_odoo.StudioCenter";
