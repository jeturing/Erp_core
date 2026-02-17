/** @odoo-module **/

import {registry} from "@web/core/registry";
import {NodeModifier, ComponentModifier} from "../../modifier";

const modifierRegistry = registry.category("modifier_views");


const PROPS = {
    type: {
        type: String, optional: true, modifierProps: {
            widget: "graph_type",
            onChange: (node, prop, value) => {
                const modeAttrs = ["area", "stacked", "smooth"];
                modeAttrs.map((prop) => {
                    if (prop in node.attrs) {
                        delete node.attrs[prop];
                    }
                });
                Object.entries(value || {}).map((data) => {
                    node.attrs[data[0]] = data[1];
                });
            },
            widgetProps: (self, node) => {
                const value = {type: "bar"};
                ["type", "area", "smooth", "stacked"].map((att) => {
                    if (att in node.attrs) {
                        value[att] = node.attrs[att];
                    }
                })
                return {value: value};
            }
        }
    }
};

export class ExtendNodeModifier extends NodeModifier {
}

ExtendNodeModifier.nodeProps = {
    ...NodeModifier.nodeProps, ...PROPS
}

ExtendNodeModifier.nodeViewStore = [
    ...NodeModifier.nodeViewStore,
    ["[graph]", ["measure", "col", "row", "type"]],
]

export class GraphModifier extends ComponentModifier {
}

GraphModifier.classes = "studio_graph_view";
GraphModifier.NodeModifier = ExtendNodeModifier;


modifierRegistry.add("graph", GraphModifier);
