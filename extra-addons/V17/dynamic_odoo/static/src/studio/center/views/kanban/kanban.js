/** @odoo-module **/

import {registry} from "@web/core/registry";
import {NodeModifier, ComponentModifier, ComponentTabsModifier} from "../../modifier";
import {DRAG_COMPONENTS} from "./drag_component";
import {FieldSelector} from "@dynamic_odoo/core/fields/field_selector/field_selector";
import {xmlToJson} from "@dynamic_odoo/core/utils/view";

const modifierRegistry = registry.category("modifier_views");
const {Component, toRaw} = owl;


class ExtendTabsModifier extends ComponentTabsModifier {

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


class OutEscList extends Component {
    propsFieldSelector(data) {
        const {model, update, readonly, followRelations} = this.props;
        const props = {
            model: model,
            readonly: readonly,
            followRelations: followRelations,
            update: (value) => {
                update({node: data.node, path: value.path});
            }
        }
        if (data.value) {
            props.value = data.value.split(".")[1];
        }
        return props;
    }
}

OutEscList.template = "dynamic_odoo.field.OutEscList";
OutEscList.components = {FieldSelector}

const appendFieldData = (viewInfo, value) => {
    const firstField = viewInfo.archJson.children[0];
    firstField.params.xpathNode(firstField, [{tag: "field", attrs: {name: value}}], "before", false, false);
}

const OutEsc = (name) => {
    return {
        type: String, optional: true, modifierProps: {
            component: OutEscList, widgetProps: (self, node) => {
                const OutEsc = [];
                OutEsc.push({node: node, value: node.attrs[name]});
                node.children.filter((child) => child.tag == "t" && child.attrs[name]).map((child) => {
                    OutEsc.push({node: child, value: child.attrs[name]});
                });
                if (OutEsc.length > 1) {
                    OutEsc.splice(0, 1);
                }
                return {
                    readonly: false,
                    followRelations: false,
                    model: self.params.viewInfo.model,
                    dataList: OutEsc,
                };
            }, onChange: (node, prop, value, params) => {
                appendFieldData(params.self.params.viewInfo, value.path);
                value.node.attrs[name] = ["record", value.path, "value"].join(".");
            }
        }
    }
}

const getDataColorNode = (node) => {
    return node.params.findNode(false, (_node) => _node.attrs && _node.attrs['data-field'] && (_node.attrs.class || "").includes("oe_kanban_colorpicker"));
}

export const PROPS = {
    t_out: OutEsc("t-out"),
    t_esc: OutEsc("t-esc"),
    name: {type: String, optional: true},
    type: {
        type: String, optional: true, modifierProps: {
            widget: "selection", widgetProps: (self, node) => {
                return {
                    value: node.attrs.type,
                    options: [['object', 'Object'], ['action', 'Action']]
                };
            }
        }
    },
    use_record_menu: {
        type: Boolean, optional: true, modifierProps: {
            widget: "toggle_switch",
            label: "Use Color Menu",
            widgetProps: (self, node) => {
                const kanbanMenu = node.params.findNode(false, (_node) => _node.attrs && _node.attrs['t-name'] == "kanban-menu");
                return {value: kanbanMenu.hasOwnProperty("tag")};
            },
            onChange: (node, prop, value, params = {}) => {
                if (value) {
                    const {app, viewInfo} = params.self.params, parser = new DOMParser();
                    const kanbanMenu = parser.parseFromString(app.rawTemplates['dynamic_odoo.kanban.KanbanMenu'].innerHTML, "text/xml");
                    const findNode = node.params.findNode(node, (_node) => _node.attrs['t-name'] == "kanban-box")
                    if (findNode) {
                        findNode.params.xpathNode(findNode, [xmlToJson(kanbanMenu)], "before", false, false);
                    }
                } else {
                    const kanbanMenu = node.params.findNode(node, (_node) => _node.attrs['t-name'] == "kanban-menu")
                    kanbanMenu.params.removeNode(kanbanMenu);
                }
            }
        }
    },
    select_field: {
        type: String, optional: true, modifierProps: {
            widget: "field_selector",
            widgetProps: (self, node) => {
                const {model} = self.params.viewInfo, {required_type} = node.attrs;
                const props = {
                    model: model,
                    value: node.attrs.name,
                    readonly: false,
                    followRelations: false
                };
                if (required_type) {
                    props.filter = (field) => field.type === required_type;
                }
                return props;
            },
            onChange: (node, prop, value, params) => {
                const viewInfo = params.self.params.viewInfo;
                node.attrs.widget = viewInfo.fields[value.path].type;
                node.attrs.name = value.path;
                appendFieldData(viewInfo, value.path);
            }
        }
    },
    kanban_image: {
        type: String, optional: true, modifierProps: {
            label: "Image from field",
            widget: "field_selector",
            widgetProps: (self, node) => {
                const {model} = self.params.viewInfo, tSrc = node.attrs['t-att-src'] || node.attrs['t-attf-src'];
                const props = {
                    model: model,
                    filter: (field) => field.type === "many2one",
                    readonly: false,
                    followRelations: false
                };
                if (tSrc) {
                    props.value = tSrc.split(",")[2].split(".")[1].trim();
                }
                return props;
            },
            onChange: (node, prop, value, params) => {
                delete node.attrs['t-attf-src'];
                const {viewInfo} = params.self.params, field = viewInfo.fields[value.path];
                node.attrs['t-att-src'] = `kanban_image('${field.relation}', 'image_128', record.${field.name}.raw_value)`;
                appendFieldData(viewInfo, value.path);
            }
        }
    },
    src: {
        type: String, optional: true, modifierProps: {
            label: "Static Image"
        }
    },
    color_field: {
        type: String, optional: true, modifierProps: {
            widget: "field_selector",
            widgetProps: (self, node) => {
                const {model} = self.params.viewInfo;
                const props = {
                    model: model,
                    filter: (field) => field.type === "integer",
                    readonly: false,
                    followRelations: false
                };
                const colorField = getDataColorNode(node);
                if (colorField) {
                    props.value = colorField.attrs['data-field'];
                }
                return props;
            },
            onChange: (node, prop, value, params) => {
                const colorField = getDataColorNode(node);
                if (colorField) {
                    colorField.attrs['data-field'] = value.path;
                }
            }
        }
    }
}

class ExtendNodeModifier extends NodeModifier {
}


ExtendNodeModifier.nodeProps = {
    ...NodeModifier.nodeProps, ...PROPS
}

ExtendNodeModifier.nodeViewStore = [
    ...NodeModifier.nodeViewStore,
    ["[field]", ["select_field", "string", "widget", "groups", "more"]],
    ["[span], [strong], [p], [h3]", (node) => {
        const view = ["t_out", "string", "more", "css"]
        const esc = node.attrs['t-esc'];
        if (esc) {
            view.splice(0, 1, "t_esc");
        }
        return view;
    }],
    ["[button]", (node) => {
        const view = ["string", "more", "css"];
        if (["action", "object"].includes(node.attrs.type)) {
            view.splice(0, 0, ...["type", "name"]);
        }
        return view;
    }],
    ["[img]", (node) => {
        const view = ["src", "kanban_image", "more", "css"];
        return view;
    }],
    ["[kanban]", (node) => {
        const view = ["edit", "create", "use_record_menu", "default_group_by", "default_order"];
        const kanbanMenu = node.params.findNode(false, (_node) => _node.attrs && _node.attrs['t-name'] == "kanban-menu");
        if (kanbanMenu) {
            view.splice(3, 0, "color_field");
        }
        return view;
    }],
]

export class KanbanModifier extends ComponentModifier {

    get componentProps() {
        const props = super.componentProps;
        props.limit = 1;
        return props;
    }
}

KanbanModifier.useStructure = true;
KanbanModifier.showNodeRoot = false;
KanbanModifier.classes = "studio_kanban_view";
KanbanModifier.ArchTemplate = "dynamic_odoo.Kanban.View.default";
KanbanModifier.NodeModifier = ExtendNodeModifier;
KanbanModifier.components = {...ComponentModifier.components, Tab: ExtendTabsModifier};

modifierRegistry.add("kanban", KanbanModifier);
