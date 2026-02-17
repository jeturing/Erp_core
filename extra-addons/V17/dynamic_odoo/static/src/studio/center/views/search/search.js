/** @odoo-module **/

import {registry} from "@web/core/registry";
import {NodeModifier, ComponentModifier, ComponentTabsModifier} from "../../modifier";
import {SearchView} from "./search_view";
import {makeContext} from "@web/core/context";
import {DRAG_COMPONENTS} from "./drag_component";

const modifierRegistry = registry.category("modifier_views");


class ExtendTabsModifier extends ComponentTabsModifier {
    get DragComponent() {
        return {...DRAG_COMPONENTS};
    }

    get tabs() {
        const tabComponents = this.tabComponent;
        return {
            [tabComponents.name]: tabComponents.data,
        }
    }
}


const PROPS = {
    field_selector: {
        type: String, optional: true, modifierProps: {
            label: "Select Field",
            widget: "field_selector",
            widgetProps: (self, node) => {
                return {
                    model: self.params.viewInfo.model,
                    filter: (field) => field.searchable,
                    readonly: false,
                    value: node.tag == "field" ? node.attrs.name : makeContext([node.attrs.context]).group_by.split(":")[0],
                    followRelations: false
                };
            },
            onChange: (node, prop, value, params) => {
                const {viewInfo} = params.self.params, field = viewInfo.fields[value.path];
                if (node.tag == "field") {
                    node.attrs.string = field.string;
                    node.attrs.name = value.path;
                } else {
                    const context = makeContext([node.attrs.context]);
                    context.group_by = value.path;
                    node.attrs.context = JSON.stringify(context);
                }
            }
        }
    },
    domain_selector: {
        type: String, optional: true, modifierProps: {
            label: "Filter",
            widget: "domain_selector",
            widgetProps: (self, node) => {
                const {model} = self.params.viewInfo, domain = node.attrs.domain, props = {model: model};
                if (domain) {
                    props.value = domain;
                }
                return props;
            },
            onChange: (node, prop, value) => {
                node.attrs.domain = value;
            }
        }
    },
    date_group_by: {
        type: String, optional: true, modifierProps: {
            label: "Group by",
            widget: "selection",
            widgetProps: (self, node) => {
                const group_by = makeContext([node.attrs.context]).group_by.split(":");
                const props = {options: [["day", "Day"], ["week", "Week"], ["month", "Month"], ["year", "Year"]]}
                if (group_by.length > 1) {
                    props.value = group_by[1]
                }
                return props;
            },
            onChange: (node, prop, value) => {
                const context = makeContext([node.attrs.context]);
                context.group_by = [context.group_by.split(":")[0], value].join(":");
                node.attrs.context = JSON.stringify(context);
            },
        }
    }
}

class ExtendNodeModifier extends NodeModifier {
}


ExtendNodeModifier.nodeProps = {
    ...NodeModifier.nodeProps, ...PROPS
}
ExtendNodeModifier.nodeViewStore = [
    ...NodeModifier.nodeViewStore,
    ["[field]", ["field_selector", "string", "more"]],
    ["[filter]", (node, viewInfo) => {
        const view = ["domain_selector", "string", "more"];
        const context = makeContext([node.attrs.context || "{}"]);
        if (context.group_by) {
            const fieldNames = context.group_by.split(":"), field = viewInfo.fields[fieldNames[0]];
            view.splice(0, 0, "field_selector");
            if (["date", "datetime"].includes(field.type)) {
                view.splice(1, 0, "date_group_by");
            }
        }
        return view;
    }],
    ["[separator]", ["more"]],
    ["[search]", []],
]

export class SearchModifier extends ComponentModifier {
}

SearchModifier.classes = "studio_search_view";
SearchModifier.NodeModifier = ExtendNodeModifier;
SearchModifier.ViewComponent = SearchView;
SearchModifier.components = {...ComponentModifier.components, Tab: ExtendTabsModifier};
SearchModifier.sortParams = {
    selector: [".items[type='field']", ".items[type='filter']", ".items[type='groupBy']"],
    lifecycle: {
        start(event, ui) {
            ui.placeholder.empty().append(ui.item.clone().children());
        },
    }
}


modifierRegistry.add("search", SearchModifier);

