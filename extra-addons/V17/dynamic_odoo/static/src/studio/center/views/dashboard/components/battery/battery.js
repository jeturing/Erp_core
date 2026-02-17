/** @odoo-module **/
import {NodeModifier, ComponentModifier} from "@dynamic_odoo/studio/center/modifier";
import {DashboardWidgets} from "@dynamic_odoo/base/views/dashboard/components/components";
import {ROOT_MODEL} from "../component_utils";

const PROPS = {
    can_resize: {type: Boolean, optional: true, modifierProps: {widget: "toggle_switch"}},
    can_drag: {type: Boolean, optional: true, modifierProps: {widget: "toggle_switch"}},
    can_export: {type: Boolean, optional: true, modifierProps: {widget: "toggle_switch"}},
    can_delete: {type: Boolean, optional: true, modifierProps: {widget: "toggle_switch"}},
    group_by: {
        type: String, optional: true, modifierProps: {
            widget: "many2one",
            onChange: (node, prop, value) => {
                node.attrs[prop.name] = value;
            },
            widgetProps: (self, node) => {
                const {model} = node.attrs;
                return {
                    relation: "ir.model.fields", value_name: "name",
                    domain: [["ttype", "in", ["selection"]], ["model", "=", model], ['store', '=', true]],
                }
            }
        },
    },
    measure: {
        type: String, optional: true, modifierProps: {
            widget: "many2one",
            onChange: (node, prop, value) => {
                node.attrs[prop.name] = value;
                node.attrs.colors = "";
            },
            widgetProps: (self, node) => {
                const {model} = node.attrs;
                return {
                    relation: "ir.model.fields", value_name: "name",
                    domain: [["store", "=", true], ["ttype", "in", ["integer", "float", "monetary"]], ["name", "!=", "id"], ["model", "=", model]],
                }
            }
        },
    },
    colors: {
        type: String, optional: true, modifierProps: {
            widget: "battery_color",
            widgetProps: (self, node) => {
                return {
                    node: node,
                }
            }
        }
    },
    root_model: ROOT_MODEL(),
}

class ExtendNodeModifier extends NodeModifier {
}

ExtendNodeModifier.nodeProps = {
    ...NodeModifier.nodeProps, ...PROPS
}

ExtendNodeModifier.nodeViewStore = [
    ...NodeModifier.nodeViewStore,
    ["[battery]", ["root_model", "root_domain", "group_by", "measure", "colors"]],
]

export class BatteryModifier extends ComponentModifier {
    get attrsRemove() {
        return ["node-id"];
    }
}

BatteryModifier.useStructure = true;
// TitleModifier.showNodeRoot = false;
BatteryModifier.NodeModifier = ExtendNodeModifier;
BatteryModifier.components = {...ComponentModifier.components, ViewComponent: DashboardWidgets.battery.component}
BatteryModifier.ArchTemplate = "dynamic_odoo.Battery.layout_1";