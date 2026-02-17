/** @odoo-module **/

import {ListModifier, ExtendNodeModifier} from "@dynamic_odoo/studio/center/views/list/list";
import {ROOT_MODEL} from "../component_utils";

const PROPS = {
    root_model: ROOT_MODEL(["domain", "record_color"], (node, prop, value, params) => {
        const fieldId = {attrs: {name: "id"}, tag: "field", children: [], parentId: node.nodeId};
        node.params.setNodeId(fieldId);
        node.children = [fieldId];
        params.self.params.app.env.bus.trigger("MODIFIER-DIALOG:RELOAD");
    }),
}

export class DashboardExtendNodeModifier extends ExtendNodeModifier {
}

DashboardExtendNodeModifier.nodeProps = {
    ...ExtendNodeModifier.nodeProps, ...PROPS
}
DashboardExtendNodeModifier.nodeViewStore = [
    ...ExtendNodeModifier.nodeViewStore,
    ["[tree]", ["editable", "create", "delete", "show_all_invisible", "root_model", "root_domain", "record_color"]],
]

export class DashboardListModifier extends ListModifier {
    get attrsRemove() {
        return [...super.attrsRemove, "node-id"];
    }
}

DashboardListModifier.NodeModifier = DashboardExtendNodeModifier;