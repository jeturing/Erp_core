/** @odoo-module **/

import {NodeModifier, ComponentModifier, ComponentTabsModifier} from "@dynamic_odoo/studio/center/modifier";
import {DashboardWidgets} from "@dynamic_odoo/base/views/dashboard/components/components";
import {xmlToJson, getTemplate} from "@dynamic_odoo/core/utils/view";
import {
    OhTitle,
    OhGrid,
    OhData,
    OhIcon,
    OhImage,
} from "@dynamic_odoo/core/widgets/drag_component/drag_component";
import {ROOT_MODEL} from "../component_utils";


const PROPS = {
    type: {
        type: String, optional: true, modifierProps: {
            widget: "selection",
            widgetProps: () => ({options: [["count", "Count"], ["sum", "Sum"], ["average", "Average"]]}),
            onChange: (node, prop, value) => {
                node.attrs[prop.name] = value;
                const {type, measure} = node.attrs;
                node.children = [{
                    tag: "t",
                    attrs: {"t-esc": "getLabel('" + type + "', '" + measure + "')"}
                }];
            },
        }
    },
    root_model: ROOT_MODEL(['domain', 'model_access_rights'], (node) => {
        const loopChild = (_node) => {
            if (_node.attrs && _node.attrs['is-data']) {
                delete _node.attrs.measure;
                delete _node.attrs.domain;
                _node.children[0].attrs['t-esc'] = "getLabel('sum', false)";
            }
            (_node.children || []).map((n) => {
                loopChild(n);
            });
        }
        loopChild(node);
    }),
    measure: {
        type: String, optional: true, modifierProps: {
            widget: "many2one",
            onChange: (node, prop, value) => {
                node.attrs[prop.name] = value;
                const {type, measure} = node.attrs;
                node.children = [{
                    tag: "t",
                    attrs: {"t-esc": "getLabel('" + type + "', '" + measure + "')"}
                }];
            },
            widgetProps: (self, node) => {
                const {model} = self.params.viewInfo;
                return {
                    relation: "ir.model.fields", value_name: "name",
                    domain: [["store", "=", true], ["ttype", "in", ["integer", "float", "monetary"]], ["name", "!=", "id"], ["model", "=", model]],
                }
            }
        },
    },
    layout: {
        type: String, optional: true, modifierProps: {
            widget: "selection",
            onChange: (node, prop, value) => {
                if (!value) return;
                const layoutTemplates = {
                    custom: "dynamic_odoo.Title.layout_custom",
                    layout_1: "dynamic_odoo.Title.layout_1",
                    layout_2: "dynamic_odoo.Title.layout_2"
                };
                node.attrs[prop.name] = value;
                node.attrs.resetNodeId = true;
                const template = getTemplate(layoutTemplates[value]);
                const parser = new DOMParser(), xml = parser.parseFromString(template, "text/xml");
                node.children = [xmlToJson(xml).children[0]]
                node.params.setNodeId(node);
            },
            widgetProps: () => ({options: [["layout_1", "Layout 1"], ["layout_2", "Layout 2"], ["custom", "Custom"]]})
        }
    },
}

const DEFAULT_PROPS = {}

class ExtendNodeModifier extends NodeModifier {
}

ExtendNodeModifier.nodeProps = {
    ...NodeModifier.nodeProps, ...PROPS
}

ExtendNodeModifier.nodePropsDefault = {
    ...NodeModifier.nodePropsDefault, ...DEFAULT_PROPS
}


ExtendNodeModifier.nodeViewStore = [
    ...NodeModifier.nodeViewStore,
    ["[span]", (node) => {
        if (node.attrs['is-data']) {
            return ["type", "measure", "more", "css"];
        }
        return ["string", "more", "css"];
    }],
    ["[title]", ["root_model", "root_domain", "layout"]]
]

class ExtendComponentTabsModifier extends ComponentTabsModifier {
    get tabs() {
        return {
            components: {
                label: "Components",
                content: [
                    {component: OhTitle, props: {}},
                    {component: OhGrid, props: {}},
                    {component: OhImage, props: {}},
                    {component: OhIcon, props: {}},
                    {component: OhData, props: {}}
                ]
            }
        }
    }
}

export class TitleModifier extends ComponentModifier {
    get attrsRemove() {
        return ["node-id"];
    }
}

TitleModifier.useStructure = true;
// TitleModifier.showNodeRoot = false;
TitleModifier.NodeModifier = ExtendNodeModifier;
TitleModifier.ArchTemplate = "dynamic_odoo.Title.layout_1";
TitleModifier.components = {
    ...ComponentModifier.components,
    ViewComponent: DashboardWidgets.title.component,
    Tab: ExtendComponentTabsModifier
};
