/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {registry, Registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {xmlToJson, jsonNodeToString} from "@dynamic_odoo/core/utils/view";
import {floorRandom} from "@dynamic_odoo/core/utils/format";
import {studioListener} from "@dynamic_odoo/core/studio_core";
import {Model, useModel} from "@web/model/model";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {FormViewDialog} from "@web/views/view_dialogs/form_view_dialog";
import {_t} from "@web/core/l10n/translation";

const studioViewRegistry = registry.category("studio_views");
const modifierRegistry = registry.category("modifier_views");
const {
    Component,
    useEffect,
    markup,
    onWillPatch,
    onWillUpdateProps,
    useRef,
    toRaw,
    status,
    onWillDestroy,
    onMounted,
    onWillUnmount,
    onWillStart,
    useState
} = owl;


patch(Registry.prototype, {
    get(key, defaultValue) {
        if (key in studioViewRegistry.content) {
            const info = studioViewRegistry.content[key];
            return info ? info[1] : defaultValue;
        }
        return super.get(key, defaultValue);
    }
});

class ViewCenterModel extends Model {
    static VIEW_CENTER_MODEL = "studio.view.center";
    static IR_UI_VIEW = "ir.ui.view";
    static IR_VIEW_MODEL = "ir.ui.menu";
    static ACTIONS_CENTER = "ir.actions.center";

    async saveView(data) {
        await this.orm.call(this.constructor.VIEW_CENTER_MODEL, "store_view", [data], {});
    }

    async resetView(data) {
        return await this.orm.call(this.constructor.VIEW_CENTER_MODEL, "reset_view", [data]);
    }

    async newView(data) {
        await this.orm.call(this.constructor.IR_UI_VIEW, "create_new_view", [data], {});
    }

    async storeAction(data) {
        await this.orm.call(this.constructor.ACTIONS_CENTER, "store_action", [data])
    }

    async undoRedoViews(viewKey, kind) {
        await this.orm.call(this.constructor.VIEW_CENTER_MODEL, "undo_redo_views", [viewKey, kind])
    }
}

class SwitchView extends Component {
    setup() {
        this.dialog = useService("dialog");
        this.modifierRegistry = modifierRegistry;
        useEffect(() => {
            this.bindAction();
        });
    }

    get viewsCtrl() {
        return {
            list: {label: "Edit List", icon: "fa fa-list-ul"},
            form: {label: "Edit Form", icon: "fa fa-address-card"},
            pivot: {label: "Edit Pivot", icon: "fa fa-table"},
            calendar: {label: "Edit Calendar", icon: "fa fa-calendar-o"},
            graph: {label: "Edit Graph", icon: "fa fa-bar-chart"},
            kanban: {label: "Edit Kanban", icon: "fa fa-th-large"},
            activity: {label: "Edit Activity", icon: "fa fa-clock-o"},
            dashboard: {label: "Edit Dashboard", icon: "fa fa-tachometer"},
            search: {label: "Edit Search View", icon: "fa fa-search"},
        }
    }

    switchView(viewType, isNew = false) {
        if (isNew) {
            return this.dialog.add(ConfirmationDialog, {
                title: _t("Confirm Active View"),
                body: markup("<h3>Do you want to active this view ?</h3>"),
                confirm: () => this.onCreateNewView.bind(this)(viewType),
                confirmLabel: _t("Active View"),
                cancel: () => {
                },
                cancelLabel: _t("No, keep it"),
            });
        }
        this.props.onChange(viewType);
    }

    async onCreateNewView(viewType) {
        const {res_model, display_name, id} = this.props.action;
        const {ArchTemplate} = this.modifierRegistry.get(viewType);
        let template = ArchTemplate ? this.__owl__.app.rawTemplates[ArchTemplate].innerHTML.trim() : `<${viewType} string="${display_name || 'Studio View'}"></${viewType}>`;
        if (viewType == "kanban") {
            template = template.replace("studio-t-name", "t-name");
        }
        const newView = {
            view_mode: viewType, action_id: id, data: {
                arch: template, model: res_model, name: `${res_model}.${viewType}.${floorRandom()}`
            }
        }
        await this.props.model.newView(newView);
        this.props.onChange(viewType, true);
    }

    bindAction() {
        const self = this, viewsCtrl = $(this.__owl__.bdom.el);
        viewsCtrl.sortable({
            stop: async function () {
                const viewsOrder = viewsCtrl.children(":not(.no_exist)").toArray().map((view) => {
                    const viewType = view.getAttribute("name");
                    return viewType == "list" ? "tree" : viewType;
                });
                await self.props.model.storeAction({
                    action_id: self.props.action.id, views_order: JSON.stringify(viewsOrder)
                });
            }
        });
    }
}

SwitchView.template = "dynamic_odoo.ViewCenter.SwitchView";

export default class ViewCenter extends Component {
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.viewService = useService("view");
        this.stackesRef = useRef("stacks");
        this.state = useState({viewType: this.uriState.view_type || "form", stacks: []});
        this.modifierRegistry = modifierRegistry;
        this.model = useModel(ViewCenterModel);
        this.stackComponents = {};
        this.dialog = useService("dialog");
        const subViewToStack = async (params) => {
            const {viewInfo, parent} = (params.detail || {});
            await this.subViewToStack(viewInfo, parent);
        }
        studioListener("VIEW_CENTER:SUBVIEW_TO_STACK", subViewToStack);
        onWillStart(async () => {
            await this.loadViews();
            this.state.stacks.push(await this.prepareStack(this.viewInfo));
        });
        onWillUpdateProps(async (nextProps) => {
            // if (this.props.resModel != nextProps.resModel) {
            const {view_type} = this.uriState;
            this.state.viewType = view_type;
            await this.reloadStack();
            // }
        });
        const onSave = this.onSave.bind(this), onReset = this.onReset.bind(this);
        onMounted(() => {
            this.env.bus.addEventListener("VIEW_CENTER:SAVE", onSave);
            this.env.bus.addEventListener("VIEW_CENTER:RESET", onReset)
        });
        onWillUnmount(() => {
            this.env.bus.removeEventListener("VIEW_CENTER:SAVE", onSave);
            this.env.bus.removeEventListener("VIEW_CENTER:RESET", onReset);
        });
    }

    get uriState() {
        return odoo.studio.getState();
    }

    get currentStack() {
        return this.state.stacks[this.state.stacks.length - 1];
    }

    get viewInfo() {
        if (!this.viewsData.views) return {};
        const {viewType} = this.state, {res_model, display_name, domain, context} = this.action;
        const {fields, relatedModels, views} = this.viewsData, viewInfo = {...views[viewType]};
        const parser = new DOMParser();
        const xml = parser.parseFromString(viewInfo.arch, "text/xml");

        viewInfo.archJson = xmlToJson(xml);
        viewInfo.fields = fields;
        viewInfo.relatedModels = relatedModels;
        viewInfo.model = res_model;
        viewInfo.string = display_name;
        viewInfo.domain = domain || [];
        viewInfo.viewType = viewType;
        viewInfo.resId = this.uriState.id;
        viewInfo.context = {...context, viewId: viewInfo.id};
        const {js_class} = viewInfo.archJson.attrs;
        if (js_class) {
            viewInfo.jsClass = js_class;
            delete viewInfo.archJson.attrs['js_class'];
        }
        return viewInfo;
    }

    setComponent(stack, component) {
        this.stackComponents[stack.key] = component;
    }

    async prepareStack(viewInfo, parent) {
        if (!viewInfo.archJson) return {}
        const {archJson} = viewInfo;
        archJson.attrs.key = archJson.attrs.key || `view_key_${floorRandom()}`;
        const stack = {
            key: archJson.attrs.key, parent: parent, viewInfo: viewInfo,
        }
        const {
            undo, redo
        } = viewInfo.isSubView && !viewInfo.store ? this.currentStack : await this.loadUndoRedo(stack.key);
        stack.undo = undo;
        stack.redo = redo;
        return stack
    }

    async loadRelatedModels(model) {
        return await this.env.services.orm.call("ir.model.fields", "load_related_models", [model]);
    }

    get actionParams() {
        const state = this.uriState;
        return {
            res_model: state.model,
            res_id: state.id,
            id: state.action,
            type: "ir.actions.act_window",
            views: [[state.view_id ? state.view_id : false, state.view_type]],
        }
    }

    async loadViews() {
        const state = this.uriState;
        this.action = await this.actionService.loadAction(state.action || this.actionParams, state);
        if (!['ir.actions.act_window'].includes(this.action.type)) {
            this.viewsData = {};
        } else {
            this.env.bus.trigger("CLEAR-CACHES");
            this.viewsData = await this.viewService.loadViews({
                context: this.action.context,
                resModel: state.model,
                views: this.action.views
            }, {actionId: this.action.id, loadActionMenus: false, loadIrFilters: false});
        }
    }

    async loadUndoRedo(viewKey) {
        const undoRedo = {},
            viewStore = await this.env.services.orm.searchRead("studio.view.center", [['view_key', '=', viewKey], ['is_current', '=', true]], ['undo', 'redo']);
        if (viewStore.length) {
            undoRedo.undo = true;
            undoRedo.redo = viewStore[0].redo;
        }
        return undoRedo;
    }

    async subViewToStack(viewInfo, parent) {
        const relatedModels = await this.loadRelatedModels(viewInfo.model);
        viewInfo.fields = relatedModels[viewInfo.model];
        viewInfo.relatedModels = relatedModels;
        const stack = await this.prepareStack(viewInfo, parent);
        if (viewInfo.store) {
            viewInfo.loadViewRef(stack.key);
        }
        this.state.stacks.push(stack);
    }

    async onChangeView(viewType, reloadViews = false) {
        if (reloadViews) {
            await this.loadViews();
        }
        toRaw(this.state).viewType = viewType;
        this.state.stacks = [await this.prepareStack(this.viewInfo)];
    }

    onBackView(index) {
        this.state.stacks.splice(index);
        this.render(true);
    }

    async onSave() {
        const {viewType} = this.state, uriState = this.uriState;
        // run patch node for stack view can not store.
        this.state.stacks.map((stack) => stack.viewInfo.isSubView && !stack.viewInfo.store && stack.viewInfo.patchNode());
        // prepare data from stack can store.
        const values = this.state.stacks.map((stack) => {
            const jsClass = stack.viewInfo.jsClass;
            if (jsClass) {
                toRaw(stack.viewInfo.archJson).attrs.js_class = jsClass;
            }
            return {
                STORE: !stack.viewInfo.isSubView || (stack.viewInfo.isSubView && stack.viewInfo.store),
                action_id: this.action?.id,
                menu_id: uriState.menu_id,
                res_model: stack.viewInfo.model,
                view_key: stack.key,
                view_id: stack.viewInfo.id,
                is_subview: stack.viewInfo.isSubView,
                view_type: viewType == "list" ? "tree" : viewType,
                arch: jsonNodeToString(stack.viewInfo.archJson), ...(this.stackComponents[stack.key]?.prepareDataToSave() || {}),
            }
        });
        await this.model.saveView(values);
        await this.reloadStack();
    }

    async onReset() {
        await this.model.resetView(this.currentStack.key);
        await this.reloadStack();
    }

    async reloadStack() {
        await this.loadViews();
        // if (this.state.canEdit) {
        this.state.stacks = [await this.prepareStack(this.viewInfo)];
        // }
    }

    async onShowAction() {
        this.dialog.add(FormViewDialog, {
            title: "Edit Window Actions",
            context: {},
            resId: this.action.id,
            resModel: "ir.actions.act_window",
            onRecordSaved: async (record) => {
                await this.reloadStack();
            },
        });
    }

    async onUndoRedo(type) {
        let currentStack = this.currentStack;
        if (currentStack.viewInfo.isSubView && !currentStack.viewInfo.store) {
            alert("Sub View")
            while (!currentStack.viewInfo.store) {
                const index = this.state.stacks.findIndex((stack) => stack.key == currentStack.key);
                currentStack = this.state.stacks[index - 1];
            }
        }
        await this.model.undoRedoViews(currentStack.key, type);
        await this.reloadStack();
    }
}

ViewCenter.template = "dynamic_odoo.ViewCenter";
ViewCenter.components = {SwitchView};
