/** @odoo-module **/

import {registry} from "@web/core/registry";
import {Domain} from "@web/core/domain"
import {conditionToDomain, domainToCondition} from "@dynamic_odoo/core/utils/domain";
import {NodeModifier, PropBoolean, TabField, ComponentTabsModifier} from "../../modifier";
import {ViewComponentModifier} from "../view_modifier";
import {OhField} from "@dynamic_odoo/core/widgets/drag_component/drag_component";

const VIRTUAL_COLUMN = "virtual_column", COLUMN_SORT = "column_sort";
const modifierRegistry = registry.category("modifier_views");

export class ExtendNodeModifier extends NodeModifier {
}

const PROPS = {
    search_in_tree: PropBoolean({label: "Search In Tree", widget: "toggle_switch"}),
    record_color: {
        type: String, optional: true,
        modifierProps: {
            widget: "record_color",
            widgetProps: (self, node) => {
                const colors = ["decoration-danger", "decoration-warning",
                    "decoration-success", "decoration-primary", "decoration-info",
                    "decoration-muted", "decoration-bf",
                    "decoration-it"], decorations = {};
                const {model} = self.params.viewInfo;
                colors.map((color) => {
                    const propColor = node.attrs[color];
                    if (propColor) {
                        decorations[color] = (new Domain(conditionToDomain(propColor))).toString();
                    }
                });
                return {value: decorations, model: model};
            },
            onChange: (node, prop, value = {}) => {
                Object.keys(value).map((decorationName) => {
                    const condition = value[decorationName];
                    node.attrs[decorationName] = domainToCondition((new Domain(condition)).toList())
                });
            }
        }
    }
}

ExtendNodeModifier.nodeProps = {
    ...NodeModifier.nodeProps, ...PROPS
}

ExtendNodeModifier.nodeViewStore = [
    ...NodeModifier.nodeViewStore,
    ["[tree]", (node, viewInfo) => {
        const view = ["editable", "create", "delete", "search_in_tree", "show_all_invisible", "record_color"];
        if (viewInfo.isSubView) {
            view.splice(3, 1);
        }
        return view;
    }],
]

ExtendNodeModifier.ShowNodeRoot = false;

export class DragField extends OhField {
}

const removeElementByClass = (classes) => {
    const elements = document.getElementsByClassName(classes);
    while (elements.length > 0) {
        elements[0].remove();
    }
}
const rmVirtualColumn = (table) => {
    table.find(`.${VIRTUAL_COLUMN}`).remove();
}
const START_CLASS = "start";
DragField.sortParams = {
    isNew: true,
    selector: ".o_list_table > thead > tr",
    withoutSelector: ".o_list_record_selector",
    nodeTemplate: (props) => {
        return "<field name='" + props.name + "' />"
    },
    params: {
        tolerance: 'intersect',
    },
    lifecycle: {
        start(event, ui, superFnc, params) {
            ui.placeholder.addClass("d-none").addClass(START_CLASS);
        },
        change(event, ui, superFnc, params) {
            const {placeholder} = ui, has_start = placeholder.hasClass(START_CLASS);
            if (has_start || (!has_start && event.target.localName !== "div")) {
                return placeholder.removeClass(START_CLASS);
            }
            const component = params.getComponent(ui.item), placeIndex = placeholder.index(),
                table = placeholder.parents("table");
            const virtualColumn = (table, index) => {
                const hasSelector = {th: false, td: false};
                table.find("tr").each((idx, tr) => {
                    const tagName = tr.firstElementChild.localName, element = document.createElement(tagName);
                    hasSelector[tagName] = tr.getElementsByClassName(".o_list_record_selector").length;
                    if (hasSelector.th && tagName != "th" && !hasSelector.td) {

                    }
                    const append = tr.children.length == (tagName == "th" ? (index + 1) : index);
                    element.classList.add(VIRTUAL_COLUMN);
                    element.classList.add(COLUMN_SORT);

                    if (tagName == "th") {
                        element.appendChild(document.createTextNode(component.props.title));
                    }
                    append ? tr.appendChild(element) : tr.insertBefore(element, tr.children[index]);
                });
            }
            const reSizeWidth = (placeholder, thVirtual) => {
                table.append(placeholder);
                params.env.bus.trigger("resize_width", {});
                placeholder.insertAfter(thVirtual);
            }
            if (placeholder.attr("index") != placeIndex) {
                rmVirtualColumn(table);
                virtualColumn(table, placeholder.index());
                reSizeWidth(placeholder, table.find(`th.${VIRTUAL_COLUMN}`));
                placeholder.attr("index", placeIndex);
            }
        },
        stop(event, ui, superFnc, params) {
            ui.placeholder.removeClass("d-none");
            superFnc(event, ui);
            const table = ui.item.parents("table");
            if (table.length) {
                rmVirtualColumn(table);
                ui.item.remove();
            }
        }
    },
}

class TabFieldExtend extends TabField {
}

TabFieldExtend.components = {...TabField.components, DragField: DragField}

class ExtendTabsModifier extends ComponentTabsModifier {
    get tabs() {
        const tabField = this.tabField, tabView = this.tabView;
        tabField.data.content[0].component = TabFieldExtend;
        return {
            [tabView.name]: tabView.data,
            [tabField.name]: tabField.data,
        }
    }
}


export class ListModifier extends ViewComponentModifier {
    prepareDataToSave() {
        const data = super.prepareDataToSave();
        data.view_type = "tree";
        return data;
    }

    get componentProps() {
        const props = super.componentProps;
        props.limit = 5;
        return props;
    }
}

// ListModifier.useStructure = true;
ListModifier.showNodeRoot = false;
ListModifier.NodeModifier = ExtendNodeModifier;
ListModifier.components = {...ViewComponentModifier.components, Tab: ExtendTabsModifier};
ListModifier.ArchTemplate = "dynamic_odoo.List.View.default";
ListModifier.classes = "studio_list_view";
ListModifier.sortParams = {
    selector: DragField.sortParams.selector,
    withoutSelector: DragField.sortParams.withoutSelector,
    params: DragField.sortParams.params,
    lifecycle: {
        start(event, ui, superFnc, params) {
            const itemWidth = ui.item.outerWidth(), itemIdx = ui.item.index(), table = ui.item.parents("table"),
                virtual_column = $("<td>").addClass(VIRTUAL_COLUMN);
            ui.placeholder.css({
                width: itemWidth,
                maxWidth: itemWidth,
                visibility: 'inherit',
            }).addClass(COLUMN_SORT).append(ui.item.children().clone());
            table.find("tr").find(`td:eq(${itemIdx})`).addClass(COLUMN_SORT).before(virtual_column);
        },
        stop(event, ui, superFnc, params) {
            superFnc(event, ui);
            const table = ui.item.parents("table");
            rmVirtualColumn(table);
            table.find(`.${COLUMN_SORT}`).removeClass(COLUMN_SORT);
        },
        change(event, ui, superFnc, params) {
            const holderIdx = ui.placeholder.index();
            ui.placeholder.parents("table").find("tr").each((idx, tr) => {
                const $tr = $(tr), column_sort = $tr.find(`td.${COLUMN_SORT}`);
                column_sort[column_sort.index() > holderIdx ? 'insertBefore' : 'insertAfter']($tr.find(`td:eq(${holderIdx})`));
            });
        },
    }
}

modifierRegistry.add("list", ListModifier);
