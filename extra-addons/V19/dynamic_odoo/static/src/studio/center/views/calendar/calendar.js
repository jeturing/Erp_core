/** @odoo-module **/

import {registry} from "@web/core/registry";
import {NodeModifier, PropBoolean, ComponentModifier} from "../../modifier";

const modifierRegistry = registry.category("modifier_views");

const getDateProps = (node, ttype = ["date", "datetime"]) => {
    const model = node.attrs.model || (odoo.studio && odoo.studio.getState().model);
    return {
        relation: "ir.model.fields", value_name: "name",
        domain: [["ttype", "in", ttype], ["name", "!=", "id"], ["model", "=", model]],
    }
}

const propDate = (types) => {
    return {
        type: String, optional: true, modifierProps: {
            widget: "many2one",
            widgetProps: (self, node) => {
                return getDateProps(node, types);
            }
        },
    }
}

const PROPS = {
    date_start: propDate(),
    date_stop: propDate(),
    date_delay: propDate(),
    color: propDate(["many2one", "selection"]),
    mode: {
        type: String, optional: true, modifierProps: {
            widget: "selection",
            widgetProps: () => ({options: [["day", "Day"], ["week", "Week"], ["month", "Month"]]}),
        }
    },
    hide_time: PropBoolean({label: "Hide Time"}),
    quick_add: PropBoolean({label: "Quick Add", widget: "toggle_switch"}),
    event_open_popup: PropBoolean({label: "Event Open Popup", widget: "toggle_switch"}),
    event_limit: {
        type: Number, optional: true, modifierProps: {
            widget: "char",
            widgetProps: (node, props) => {
                return {type: "number"}
            }
        }
    },
};

export class ExtendNodeModifier extends NodeModifier {
}

ExtendNodeModifier.nodeProps = {
    ...NodeModifier.nodeProps, ...PROPS
}

ExtendNodeModifier.nodeViewStore = [
    ...NodeModifier.nodeViewStore,
    ["[calendar]", ["date_start", "date_stop", "date_delay", "color", "mode", "event_limit", "hide_time", "create", "delete", "quick_add", "event_open_popup"]],
]

export class CalendarModifier extends ComponentModifier {
}

CalendarModifier.classes = "studio_calendar_view";
CalendarModifier.NodeModifier = ExtendNodeModifier;
CalendarModifier.ArchTemplate = "dynamic_odoo.Calendar.View.default";


modifierRegistry.add("calendar", CalendarModifier);
