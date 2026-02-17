/** @odoo-module **/

import {GraphModifier, ExtendNodeModifier} from "@dynamic_odoo/studio/center/views/graph/graph";
import {ROOT_MODEL} from "../component_utils";

const PROPS = {
    root_model: ROOT_MODEL(["domain", "measure", "col", "row"], (node) => {
        node.children = [];
    }),
}

export class DashboardExtendNodeModifier extends ExtendNodeModifier {
}

DashboardExtendNodeModifier.nodeProps = {
    ...ExtendNodeModifier.nodeProps, ...PROPS
}
DashboardExtendNodeModifier.nodeViewStore = [
    ...ExtendNodeModifier.nodeViewStore,
    ["[graph]", ["root_model", "root_domain", "measure", "col", "row", "type"]],
]

export class DashboardGraphModifier extends GraphModifier {
    get attrsRemove() {
        return [...super.attrsRemove, "node-id"];
    }
}

DashboardGraphModifier.NodeModifier = DashboardExtendNodeModifier;