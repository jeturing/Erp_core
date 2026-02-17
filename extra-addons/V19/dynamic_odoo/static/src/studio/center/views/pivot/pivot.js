/** @odoo-module **/

import {registry} from "@web/core/registry";
import {NodeModifier, ComponentModifier} from "../../modifier";
import {KanbanModifier} from "../kanban/kanban";

const modifierRegistry = registry.category("modifier_views");

export class ExtendNodeModifier extends NodeModifier {
}

ExtendNodeModifier.nodeViewStore = [
    ...NodeModifier.nodeViewStore,
    ["[pivot]", ["measure", "col", "row"]],
]

export class PivotModifier extends ComponentModifier {
}

PivotModifier.classes = "studio_pivot_view";
PivotModifier.NodeModifier = ExtendNodeModifier;


modifierRegistry.add("pivot", PivotModifier);
