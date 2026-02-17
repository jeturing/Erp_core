/** @odoo-module **/

import {registry} from "@web/core/registry";
import {DashboardController} from "./dashboard_controller";
import {DashboardModel} from "./dashboard_model";
import {DashboardRenderer} from "./dashboard_renderer";
import {DashboardArchParser} from "./dashboard_arch_parser";


export const DashboardView = {
    type: "dashboard",
    display_name: "Dashboard",
    icon: "fa fa-tachometer",
    Controller: DashboardController,
    Renderer: DashboardRenderer,
    ArchParser: DashboardArchParser,
    multiRecord: true,
    Model: DashboardModel,
    props: (genericProps, view) => {
        const {ArchParser} = view;
        const {arch, relatedModels, resModel} = genericProps;
        const archInfo = new ArchParser().parse(arch, relatedModels, resModel);

        return {
            ...genericProps,
            Model: view.Model,
            Renderer: view.Renderer,
            // buttonTemplate: view.buttonTemplate,
            archInfo,
        };
    },
};

registry.category("views").add("dashboard", DashboardView);
