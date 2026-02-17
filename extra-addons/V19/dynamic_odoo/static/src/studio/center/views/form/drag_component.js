/** @odoo-module **/
import {
    OhField,
    OhGrid,
    DragComponent,
    OhTitle,
    OhIcon,
    OhImage
} from "@dynamic_odoo/core/widgets/drag_component/drag_component";
import {dispatchEvent} from "@dynamic_odoo/core/studio_core";
import {floorRandom} from "@dynamic_odoo/core/utils/format";

class OhGroup extends DragComponent {
}

OhGroup.title = "Group";
OhGroup.icon = "fa fa-object-group";
OhGroup.sortParams = {
    ...DragComponent.sortParams,
    useHelper: true,
    selector: ".o_form_editable, .o_form_sheet, .tab-content",
    nodeTemplate: "dynamic_odoo.DragCom.NodeTemplate.Group",
    replaceTemplate: "dynamic_odoo.DragCom.ReplaceTemplate.Group",
    replaceClass: "rp_group",
    helperClass: "row grid_drag"
}

class OhNotebook extends DragComponent {
}

OhNotebook.title = "Notebook";
OhNotebook.icon = "fa fa-leanpub";
OhNotebook.sortParams = {
    ...DragComponent.sortParams,
    selector: ".o_form_sheet",
    nodeTemplate: "dynamic_odoo.DragComponent.Notebook",
    replaceTemplate: "dynamic_odoo.DragCom.ReplaceTemplate.Notebook",
    replaceClass: "rp_notebook",
}

class OhText extends DragComponent {
}

OhText.title = "Text";
OhText.icon = "fa fa-font";
OhText.sortParams = {
    ...DragComponent.sortParams,
    useHelper: true,
    selector: ".ROW > .can_drag",
    nodeTemplate: "dynamic_odoo.DragComponent.Text",
    // replaceTemplate: "dynamic_odoo.DragComponent.Text",
    replaceClass: "rp_text"
}

class OhButton extends DragComponent {
}

OhButton.title = "Button";
OhButton.icon = "fa fa-gg";
OhButton.sortParams = {
    ...DragComponent.sortParams,
    selector: ".o_statusbar_buttons",
    nodeTemplate: "dynamic_odoo.DragComponent.Button",
    replaceTemplate: "dynamic_odoo.DragComponent.Button",
    replaceClass: "rp_button"
}

class OhGridExtend extends OhGrid {
}

OhGridExtend.sortParams = {
    ...OhGrid.sortParams,
    selector: ".o_form_sheet, .tab-pane",
    helperClass: "row grid_drag"
}

class OhTitleExtend extends OhTitle {
}

OhTitleExtend.sortParams = {
    ...OhTitle.sortParams,
    selector: ".ROW > .can_drag",
}

class OhImageExtend extends OhImage {
}

OhImageExtend.sortParams = {
    ...OhImage.sortParams,
    selector: ".ROW > .can_drag",
}

class OhIconExtend extends OhIcon {
}

OhIconExtend.sortParams = {
    ...OhIcon.sortParams,
    selector: ".ROW > .can_drag",
}

class OhFieldExtend extends OhField {

}

OhFieldExtend.sortParams = {
    ...OhField.sortParams,
    selector: ".container, .o_inner_group, .col, .o_form_statusbar, .can_drag",
    nodeTemplate: (props) => {
        const nodeProps = props.props || {}, field = {
            name: `x_field_${floorRandom()}`,
            type: props.type || props.name, ...nodeProps,
        }
        dispatchEvent("STUDIO_FORM:NEW_FIELD", {field: field}, props.el);
        const stringProps = Object.keys(nodeProps).map((propName) => `${propName}="${nodeProps[propName]}"`).join(" ");
        return `<Field name="${field.name}" ${stringProps} />`;
    },
    lifecycle: {
        stop(event, ui, superFnc, params) {
            const item = ui.item, groupWrap = item.parents(".o_inner_group"), WRAP_FIELD_CLASS = ".o_wrap_field";
            if (groupWrap.length && groupWrap.find(WRAP_FIELD_CLASS).length) {
                const propsXpath = {el: ui.item.next(WRAP_FIELD_CLASS), position: "before"}
                if (!propsXpath.el.length) {
                    propsXpath.el = ui.item.prev(WRAP_FIELD_CLASS);
                    propsXpath.position = "after";
                }
                let nodeXpath = propsXpath.el.children().toArray().map((child) => $(child).find("> *[node-id]").attr("node-id")).filter((xpath) => xpath);
                if (!nodeXpath.length) {
                    nodeXpath = [propsXpath.el.attr("node-id")];
                }
                if (nodeXpath.length) {
                    propsXpath.nodeXpath = nodeXpath[propsXpath.position == "before" ? 0 : (nodeXpath.length - 1)];
                    params.params = propsXpath;
                }
            }
            superFnc(event, ui, params);
        }
    }
}
export const DRAG_COMPONENTS = {
    OhButton,
    OhNotebook,
    OhText,
    OhGroup,
    OhField: OhFieldExtend,
    OhIcon: OhIconExtend,
    OhImage: OhImageExtend,
    OhTitle: OhTitleExtend,
    OhGrid: OhGridExtend
}