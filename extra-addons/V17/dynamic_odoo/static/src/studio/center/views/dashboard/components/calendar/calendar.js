/** @odoo-module **/

import {CalendarModifier, ExtendNodeModifier} from "@dynamic_odoo/studio/center/views/calendar/calendar";
import {ROOT_MODEL} from "../component_utils";

const PROPS = {
    root_model: ROOT_MODEL(["domain", "date_start", "date_stop", "date_delay", "color"], (node) => {
        node.attrs.date_start = "create_date";
        node.children = [];
    }),
}

export class DashboardExtendNodeModifier extends ExtendNodeModifier {
}

ExtendNodeModifier.nodeProps = {
    ...ExtendNodeModifier.nodeProps, ...PROPS
}
ExtendNodeModifier.nodeViewStore = [
    ...ExtendNodeModifier.nodeViewStore,
    ["[calendar]", ["root_model", "root_domain", "date_start", "date_stop", "date_delay", "color", "mode", "event_limit", "hide_time", "create", "delete", "quick_add", "event_open_popup"]],
]

export class DashboardCalendarModifier extends CalendarModifier {
    get attrsRemove() {
        return [...super.attrsRemove, "node-id"];
    }
}

DashboardCalendarModifier.NodeModifier = DashboardExtendNodeModifier
