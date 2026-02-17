/** @odoo-module **/

import {ReportViewer} from '../viewer/report_viewer';
import {stringToJson} from "@dynamic_odoo/core/utils/view";
import {DRAG_COMPONENTS} from "../drag_component";
import {Domain} from "@web/core/domain";
import {FieldOptionsWidget} from "../widgets/field_options_widget/field_options_widget";
import {conditionToDomain, domainToCondition} from "@dynamic_odoo/core/utils/domain";

import {
    getOptions,
    QWEB_SYNTAX,
    DYNAMIC_MODEL,
    NodeModifierTemplate,
    ComponentModifierTemplate,
    ComponentTabsModifierTemplate,
    prepareDataOeContext
} from "@dynamic_odoo/studio/center/template/template_modifier";


const {onWillUpdateProps, useEffect, onWillStart} = owl;

class ExtendTabsModifier extends ComponentTabsModifierTemplate {
    get DragComponent() {
        return {...DRAG_COMPONENTS};
    }

    get tabs() {
        const tabView = this.tabView, tabComponents = this.tabComponent;
        return {
            [tabView.name]: tabView.data, [tabComponents.name]: tabComponents.data,
        }
    }
}

export const PROPS = {
    table_data: {
        type: String, optional: true, modifierProps: {
            widget: "field_selector", label: "Choose data for Table", widgetProps: (self, node) => {
                const modelName = "choose_table_data";
                DYNAMIC_MODEL[modelName] = prepareDataOeContext(self, node);
                const props = {model: modelName, allowEmpty: true, readonly: false};
                return props;
            }, onChange: (node, prop, value, params) => {
                const viewTableData = stringToJson(params.self.params.app.rawTemplates['dynamic_odoo.DragComponent.Table.LoadData'].innerHTML);
                viewTableData.attrs[QWEB_SYNTAX.tForeach] = value.path;
                const findNode = node.params.findNode(node, (_node) => _node.tag == "tbody");
                if (findNode) {
                    findNode.children = [viewTableData];
                    delete node.attrs["need_data"];
                }
            }
        }
    },
    img_field: {
        type: String, optional: true, modifierProps: {
            widget: "field_selector", label: "Choose Image Data", widgetProps: (self, node) => {
                const modelName = "choose_img_model", src = node.attrs[QWEB_SYNTAX.tAttSrc];
                DYNAMIC_MODEL[modelName] = prepareDataOeContext(self, node);
                const props = {
                    model: modelName,
                    allowEmpty: true,
                    filter: (field) => ["many2one", "binary", "image"].includes(field.type),
                    readonly: false
                };
                if (src && src.indexOf("image_data_uri") >= 0) {
                    props.value = src.slice(15, src.length - 1)
                }
                return props;
            }, onChange: (node, prop, value, params) => {
                value ? (node.attrs[QWEB_SYNTAX.tAttSrc] = `image_data_uri(${value.path})`) : (delete node.attrs[QWEB_SYNTAX.tAttSrc]);
            }
        }
    },
    t_field: {
        type: String, optional: true, modifierProps: {
            widget: "field_selector", label: "Choose Field", widgetProps: (self, node) => {
                const modelName = "choose_field_model", value = node.attrs[QWEB_SYNTAX.tField];
                DYNAMIC_MODEL[modelName] = prepareDataOeContext(self, node);
                const props = {model: modelName, allowEmpty: true, readonly: false};
                if (value) {
                    props.value = value;
                }
                return props;
            }, onChange: (node, prop, value, params) => {
                if (!value.path && !value.fieldInfo) {
                    delete node.attrs[QWEB_SYNTAX.tField];
                    delete node.attrs[QWEB_SYNTAX.tOptions];
                } else {
                    const options = getOptions(node);
                    if (options.widget) {
                        delete options.widget;
                        node.attrs[QWEB_SYNTAX.tOptions] = JSON.stringify(options);
                    }
                    node.attrs[QWEB_SYNTAX.tField] = value.path;
                }
            }
        }
    }, "t-if": {
        type: String, optional: true, modifierProps: {
            label: "Visible If", widget: "domain_selector", widgetProps: (self, node) => {
                const modelName = "visible_if_model", props = {model: modelName, isDynamicModel: true},
                    value = node.attrs[QWEB_SYNTAX.tIf];
                DYNAMIC_MODEL[modelName] = prepareDataOeContext(self, node);
                if (value) {
                    if (!(value.split(".")[0] in DYNAMIC_MODEL[modelName])) {
                        props.isDynamicModel = false;
                    }
                    try {
                        props.value = new Domain(conditionToDomain(value)).toString();
                    } catch {
                        props.value = value;
                    }
                }
                return props;
            }, onChange: (node, prop, value, params) => {
                if (value) {
                    try {
                        node.attrs[QWEB_SYNTAX.tIf] = domainToCondition(new Domain(value).toJson());
                    } catch {
                        node.attrs[QWEB_SYNTAX.tIf] = value;
                    }
                } else {
                    delete node.attrs[QWEB_SYNTAX.tIf]
                }
            }
        }
    }, add_to_print: {
        type: Boolean, optional: true, modifierProps: {
            widget: "toggle_switch", label: "Add to the 'Print' menu",
            widgetProps: (self, node) => {
                const {viewInfo} = node.params.modifier.props;
                return {value: viewInfo.params.binding_model_id ? true : false}
            },
            onChange: async (node, prop, value, params) => {
                const {viewInfo, model} = node.params.modifier.props;
                await model.orm.call("ir.actions.report", value ? "create_action" : "unlink_action", [viewInfo.reportId])
            }
        }
    },
    class: {},
    widget: {
        type: String, optional: true, modifierProps: {
            widget: "selection", widgetProps: (self, node) => {
                const {params} = self.params.viewInfo, props = {}, options = getOptions(node);
                if (params.fieldWidgets) {
                    props.options = Object.keys(params.fieldWidgets).map((widget) => [widget, widget.charAt(0).toUpperCase() + widget.slice(1)]);
                }
                if (options.widget) {
                    props.value = options.widget;
                }
                return props;
            }, onChange: (node, prop, value, params) => {
                const options = getOptions(node);
                options.widget = value;
                if (value == "contact") {
                    node.attrs.class = "is_address";
                }
                node.attrs[QWEB_SYNTAX.tOptions] = JSON.stringify(options);
            }
        }
    }, field_options: {
        type: String, optional: true, modifierProps: {
            component: FieldOptionsWidget, widgetProps: (self, node) => {
                const {params} = self.params.viewInfo, {fieldWidgets} = params, props = {};
                const options = getOptions(node);
                if (Object.keys(options).length) {
                    props.value = options;
                }
                if (options.widget && fieldWidgets) {
                    props.options = {...fieldWidgets[options.widget]};
                }
                return props;
            }, onChange: (node, prop, value, params) => {
                const options = getOptions(node);
                if (typeof value == "undefined") {
                    delete options[value.name];
                }
                options[value.name] = value.value;
                node.attrs[QWEB_SYNTAX.tOptions] = JSON.stringify(options);
            }
        }
    }, report_more: {
        type: String, optional: true, modifierProps: {
            widget: "more", onChange: (node, prop, value) => {
            }, widgetProps: (self, node) => {
                return {
                    domain: () => [['id', '=', self.params.viewInfo.reportId]],
                    title: "Change Report Property",
                    resModel: "ir.actions.report",
                    remove: false,
                    more: true,
                };
            }
        },
    },
    number_option: {
        type: Number, optional: true, modifierProps: {
            widgetProps: (self, node) => {
                return {
                    value: node.children.length,
                };
            },
            onChange: (node, prop, value, params) => {
                const options = node.children;
                if (value < options.length) {
                    options.splice(value, 1);
                } else {
                    const size = value - options.length;
                    for (let i = 0; i < size; i++) {
                        const {app} = params.self.params;
                        const option = stringToJson(app.rawTemplates['dynamic_odoo.DragComponent.CheckBoxList.option'].innerHTML);
                        options.push(option);
                    }
                }
            }
        }
    },
    circle: {
        type: Boolean, optional: true, modifierProps: {
            widget: "toggle_switch",
            label: "Circle",
        }
    },
    rowspan: {
        type: Number, optional: true,
    },
    colspan: {
        type: Number, optional: true,
    }
}

class NodeModifierExtends extends NodeModifierTemplate {

}

NodeModifierExtends.nodeProps = {
    ...NodeModifierTemplate.nodeProps, ...PROPS
}

NodeModifierExtends.nodeViewStore = [...NodeModifierTemplate.nodeViewStore,
    ["[h1], [h2], [h3], [h4], [h5], [h6], [strong], [p], [span]", (node) => {
        if ((node.attrs.class || "").includes("rp_checkbox")) {
            return ["circle", "t-if", "css", "more"];
        }
        const view = ["string", "t_field", "t-if", "groups", "css", "more"];
        if (node.attrs[QWEB_SYNTAX.tField]) {
            view.splice(2, 0, "widget");
            const options = getOptions(node);
            if (options.widget) {
                view.splice(3, 0, "field_options");
            }
        }
        return view;
    }],
    ["[th], [td]", ["colspan", "rowspan", "string", "t-if", "groups", "css", "more"]],
    ["[tr]", ["css"]],
    ["[img]", ["img_field", "t-if", "css", "more"]],
    ["[div]", (node) => {
        const divViewStore = NodeModifierTemplate.nodeViewStore.filter((viewStore) => viewStore[0] == "[div]")[0];
        const superView = divViewStore[1](node);
        const componentName = node.attrs['component'];
        superView.splice(superView.length - 1, 1)
        const view = [...superView, "t-if", "groups", "more"], options = getOptions(node);
        if (options.widget) {
            view.splice(0, 0, ...["t_field", "widget", "field_options"]);
        }
        switch (componentName) {
            case "checkbox_list":
                view.splice(0, 0, "number_option");
                break;
        }
        return view;
    }],
    ["[table]", (node) => {
        const view = ["css", "more"], needData = node.attrs['need_data'];
        if (needData) {
            view.splice(0, 0, "table_data");
        }
        return view;
    }],
    ["[a]", ["string", "href", "t_field", "t-if", "groups", "css", "more"]],
    ["[html]", ["add_to_print", "report_more"]],]

export class ReportModifier extends ComponentModifierTemplate {

    setup() {
        super.setup();
        onWillStart(async () => {
            await this.loadCanUndoRedo();
        });
        onWillUpdateProps(async (nextProps) => {
            await this.loadCanUndoRedo();
        });
        const callBack = async () => {
            this.nodes = {};
            await this.props.model.resetTemplate(this.key);
            await this.reload();
        }
        useEffect(() => {
            this.env.bus.addEventListener("REPORT_CENTER:RESET", callBack);
            return () => this.env.bus.removeEventListener("REPORT_CENTER:RESET", callBack);
        });
    }

    // get key() {
    //     return this.props.viewInfo.reportId;
    // }

    get loadTemplateProps() {
        const props = super.loadTemplateProps;
        props.context.IS_REPORT = true;
        return props;
    }

    get viewComponentProps() {
        const props = super.viewComponentProps;
        props.model = this.props.model;
        props.reloadReport = this.reload.bind(this);
        props.can_undo = this.canUndoRedo?.can_undo;
        props.can_redo = this.canUndoRedo?.can_redo;
        props.templateKey = this.key;
        props.bindAction = this.bindAction.bind(this);
        return props;
    }

    async loadCanUndoRedo() {
        this.canUndoRedo = await this.props.model.canUndoRedo(this.key);
    }

    bindStyle() {
        super.bindStyle();
        if (this.currentEl.find("> address").length) {
            this.currentEl.addClass("is_address");
        }
    }
}

ReportModifier.classes = "studio_report_view";
ReportModifier.components = {...ComponentModifierTemplate.components, Tab: ExtendTabsModifier};
ReportModifier.NodeModifier = NodeModifierExtends;
ReportModifier.ViewComponent = ReportViewer;




