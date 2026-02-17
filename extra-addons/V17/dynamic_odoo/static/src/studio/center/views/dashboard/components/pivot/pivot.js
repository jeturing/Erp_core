/** @odoo-module **/

import {PivotModifier, ExtendNodeModifier} from "@dynamic_odoo/studio/center/views/pivot/pivot";
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
    ["[pivot]", ["root_model", "root_domain", "measure", "col", "row"]],
]

export class DashboardPivotModifier extends PivotModifier {
    get attrsRemove() {
        return [...super.attrsRemove, "node-id"];
    }
}

DashboardPivotModifier.NodeModifier = DashboardExtendNodeModifier;
