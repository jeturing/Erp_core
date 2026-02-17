/** @odoo-module **/

import {View} from "@web/views/view";
import {useService} from "@web/core/utils/hooks";
import {xmlToJson} from "@dynamic_odoo/core/utils/view";

const {Component, useState, onWillUpdateProps, onWillStart, xml} = owl;

export class ViewController extends Component {
    static viewType = "list";
    static viewTypeSwitch = "form";
    static ViewComponentSwitch = false;

    setup() {
        this.state = useState({viewType: this.constructor.viewType, resId: false});
        this.viewService = useService("view");
        this.actionService = useService("action");
        onWillStart(async () => {
            await this.loadViews();
        });
        // onWillUpdateProps(async (nextProps) => {
        //     if (nextProps.resModel != this.props.resModel) {
        //         this.__owl__.children = {};
        //         await this.loadViews();
        //         // this.render(true);
        //     }
        // });
    }

    get componentInfo() {
        return {
            Component: this.isViewBase ? View : this.constructor.ViewComponentSwitch,
            componentProps: this.componentProps
        };
    }

    get domain() {
        return [];
    }

    get isViewBase() {
        return ["list", "kanban", "form", "pivot", "calendar", "activity", "graph"].includes(this.state.viewType);
    }

    get componentProps() {
        const {viewType, resId} = this.state, {res_model, context} = this.action, {
            relatedModels,
            fields,
            views
        } = this.viewsData;
        const props = {
            type: viewType,
            arch: views[viewType]?.arch,
            resModel: res_model,
            relatedModels: relatedModels,
            fields: fields,
            domain: this.domain,
            loadIrFilters: true,
            views: [[false, "search"]],
            irFilters: [],
            noBreadcrumbs: true,
            selectRecord: this.selectRecord.bind(this),
            createRecord: this.createRecord.bind(this),
            resId: resId,
            context: context
        };
        return props;
    }

    async selectRecord(resId) {
        this.switchView({resId});
    }

    async createRecord() {
        this.switchView({resId: false});
    }

    async loadViews() {
        const state = odoo.studio.getState();
        this.action = await this.actionService.loadAction(this.constructor.actionXmlID, state);
        const {context, res_model, views, id} = this.action;
        this.viewsData = await this.viewService.loadViews(
            {context: context, resModel: res_model, views: views},
            {actionId: id, loadActionMenus: false, loadIrFilters: true}
        );
    }

    switchView(params) {
        this.state.resId = params.resId;
        if (this.constructor.viewTypeSwitch) {
            this.state.viewType = this.constructor.viewTypeSwitch;
        }
    }
}

ViewController.template = xml`<div t-att-class="props.classes"><t t-set="comInfo" t-value="componentInfo" /><t t-component="comInfo.Component" t-key="Math.random()" t-props="comInfo.componentProps" /></div>`;
