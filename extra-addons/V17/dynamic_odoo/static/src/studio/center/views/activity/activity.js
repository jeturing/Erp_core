/** @odoo-module **/

import {registry} from "@web/core/registry";
import {NodeModifier, ComponentModifier} from "../../modifier";

const modifierRegistry = registry.category("modifier_views");

class ActivityNodeModifier extends NodeModifier {
}

ActivityNodeModifier.nodeViewStore = [
    ...NodeModifier.nodeViewStore,
    ["[activity]", []],
]

export class ActivityModifier extends ComponentModifier {
}

ActivityModifier.classes = "studio_activity_view";
ActivityModifier.NodeModifier = ActivityNodeModifier;


modifierRegistry.add("activity", ActivityModifier);

