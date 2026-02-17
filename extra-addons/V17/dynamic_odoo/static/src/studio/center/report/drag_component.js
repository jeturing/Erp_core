/** @odoo-module **/
import {
    OhGrid,
    DragComponent,
    OhText,
    OhTitle,
    OhLink,
    OhIcon,
    OhImage
} from "@dynamic_odoo/core/widgets/drag_component/drag_component";

const {Component, onWillPatch, useState, useEffect, onMounted} = owl;

class OhTable extends DragComponent {

}

OhTable.icon = "fa fa-table";
OhTable.title = "Table";
OhTable.sortParams = {
    ...DragComponent.sortParams,
    selector: ".report_content main .page",
    useHelper: true,
    nodeTemplate: "dynamic_odoo.DragComponent.Table",
}


const VIRTUAL_COLUMN = "virtual_column";

const USE_TABLE_HELPER = (funcName = "addClass") => {
    $(document).find(".report_content table")[funcName]("table_helper");
}

class OhColumns extends DragComponent {
    setup() {
        super.setup();
        useEffect(() => {
            this.el.addEventListener("mouseover", () => USE_TABLE_HELPER());
            this.el.addEventListener("mouseout", () => USE_TABLE_HELPER("removeClass"));
        });
    }

}

const rmVirtualColumn = (table) => {
    table.find(`.${VIRTUAL_COLUMN}`).remove();
}
OhColumns.icon = "fa fa-th-list";
OhColumns.title = "Columns";
OhColumns.sortParams = {
    ...DragComponent.sortParams,
    selector: ".report_content .page table > thead > tr",
    lifecycle: {
        start(event, ui, superFnc, params) {
        },
        change(event, ui, superFnc, params) {
            const {placeholder} = ui, table = placeholder.parents("table");
            rmVirtualColumn(table);
            const virtualColumn = (table, index) => {
                table.find("tr").each((idx, tr) => {
                    const tagName = $(tr).find(" > *:not(div)")[0].localName,
                        element = document.createElement(tagName),
                        append = tr.children.length == (tagName == "th" ? (index + 1) : index);
                    const nodeXpath = (append ? tr : $(tr).find("> *:not(div)")[index]);
                    element.classList.add(VIRTUAL_COLUMN);
                    element.appendChild(document.createTextNode("New Column"));
                    element.setAttribute("node-xpath", nodeXpath.getAttribute("node-id"));
                    element.setAttribute("templateId", tr.getAttribute("data-oe-id"));
                    element.setAttribute("position", append ? "append" : "before");
                    element.setAttribute("parentId", tr.getAttribute("node-id"));
                    append ? tr.appendChild(element) : tr.insertBefore(element, tr.children[index]);
                });
            }
            virtualColumn(table, placeholder.index());
            placeholder.addClass("d-none");
        },
        async stop(event, ui, superFnc, params) {
            USE_TABLE_HELPER("removeClass");
            if (!ui.item.parents(".report_content").length) {
                return;
            }
            // can tim realNode
            const {modifier} = params, table = ui.item.addClass("d-none").parents("table");
            const nodeCreator = {
                th: {selector: `th.${VIRTUAL_COLUMN}`, tag: "th", text: "New Column"},
                td: {selector: `td.${VIRTUAL_COLUMN}:eq(0)`, tag: "td"}
            };

            Object.values(nodeCreator).map((props) => {
                const element = table.find(props.selector), {tag, text} = props;
                props.parentId = element.attr("parentId");
                props.nodeXpath = element.attr("node-xpath");
                props.templateId = element.attr("templateId");
                props.position = element.attr("position");
                props.noveMove = {
                    tag: tag, attrs: {},
                    children: [
                        {tag: "span", attrs: {}, children: ["New Column"]}
                    ],
                    parentId: props.parentId
                };
                props.params = [props.nodeXpath, [props.noveMove], props.position];
                modifier.setNodeId(props.noveMove);
            });
            await modifier._onXpathNode(...nodeCreator.th.params, false, false);
            await modifier._onXpathNode(...nodeCreator.td.params, false, false);
            await modifier._saveTemplate(nodeCreator.td.templateId);
            await modifier.loadTemplate(nodeCreator.td.templateId, true);
            await modifier.reload(false);
            const spanField = nodeCreator.td.noveMove.children[0];
            modifier.state.node = modifier.getNode(spanField.nodeId);
        }
    },
}

class OhGridExtend extends OhGrid {

}

OhGridExtend.sortParams = {
    ...OhGrid.sortParams,
    selector: "main > .header, main > .article > div, main > .footer",
}

class OhTextExtend extends OhText {

}

OhTextExtend.sortParams = {
    ...OhText.sortParams,
    helperClass: "helper_inline",
    selector: ".container, div[class*='col-'], .col, .report_content main th, .report_content .can_drag",
}

class OhIconExtend extends OhIcon {

}

OhIconExtend.sortParams = {
    ...OhIcon.sortParams,
    selector: ".container, div[class*='col-'], .col, .report_content main th, .report_content .can_drag",
}

class OhLinkExtend extends OhLink {
}

OhLinkExtend.sortParams = {
    ...OhLink.sortParams,
    helperClass: "helper_inline",
    replaceTemplate: "<a href='https://odoo-studio.com' target='new'>New link</a>",
    selector: ".container, div[class*='col-'], .col, .report_content main th, .report_content .can_drag",
}

class CheckBoxList extends DragComponent {

}

CheckBoxList.title = "CheckBox List";
CheckBoxList.icon = "fa fa-list-alt",
CheckBoxList.sortParams = {
    ...DragComponent.sortParams,
    useHelper: true,
    nodeTemplate: "dynamic_odoo.DragComponent.CheckBoxList",
    replaceTemplate: "dynamic_odoo.DragComponent.CheckBoxList",
    selector: "main > .header, main > .article > div, main > .footer, .can_drag"
}

class OhImageExtend extends OhImage {

}

OhImageExtend.sortParams = {
    ...OhImage.sortParams,
    nodeTemplate: () => {
        return `<img need_data="true" src="/dynamic_odoo/static/img/playlist_png.png" />`
    }
}

export const DRAG_COMPONENTS = {
    OhTextExtend,
    OhIconExtend,
    OhTitle,
    OhLinkExtend,
    OhImageExtend,
    CheckBoxList,
    OhGridExtend,
    OhTable,
    OhColumns,
}