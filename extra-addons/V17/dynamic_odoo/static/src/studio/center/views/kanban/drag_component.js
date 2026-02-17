/** @odoo-module **/
import {
    OhField,
    OhGrid,
    DragComponent,
    OhTitle,
    OhIcon,
    OhImage
} from "@dynamic_odoo/core/widgets/drag_component/drag_component";


const prepareProps = (viewInfo, attr = "type", value = "") => {
    const {fields} = viewInfo;
    return {readonly: !Object.values(fields).filter((field) => field[attr] == value).length};
};

const defaultSortParams = (attr, value, widget) => {
    return {
        ...DragComponent.sortParams,
        useHelper: true,
        selector: ".can_drag",
        nodeTemplate: (props) => {
            const fields = props.viewInfo.fields;
            const defaultField = Object.values(fields).filter((field) => field[attr] == value)[0];
            return `<Field name='${defaultField.name}' widget='${widget}' required_type="${value}" />`;
        },
    }
}

class OhTags extends DragComponent {
}

OhTags.title = "Tags";
OhTags.icon = "fa fa-tags";
OhTags.prepareProps = (viewInfo) => prepareProps(viewInfo, "type", "many2many");
OhTags.sortParams = defaultSortParams("type", "many2many", "many2many_tags");


class OhPriority extends DragComponent {
}

OhPriority.title = "Priority";
OhPriority.icon = "fa fa-ticket";
OhPriority.prepareProps = (viewInfo) => prepareProps(viewInfo, "type", "selection");
OhPriority.sortParams = defaultSortParams("type", "selection", "priority");


class OhActivities extends DragComponent {
}

OhActivities.title = "Activities";
OhActivities.icon = "fa fa-ticket";
OhActivities.prepareProps = (viewInfo) => prepareProps(viewInfo, "name", "activity_ids");
OhActivities.sortParams = defaultSortParams("name", "activity_ids", "kanban_activity");


class OhLabel extends DragComponent {
}

OhLabel.title = "Label";
OhLabel.icon = "fa fa-ticket";
OhLabel.prepareProps = (viewInfo) => prepareProps(viewInfo, "type", "selection");
OhLabel.sortParams = defaultSortParams("type", "selection", "label_selection");


class OhText extends DragComponent {
}

OhText.title = "Text";
OhText.icon = "fa fa-text-width";
OhText.sortParams = {
    ...DragComponent.sortParams,
    useHelper: true,
    selector: ".can_drag",
    nodeTemplate: (props) => {
        return `<span>New Text</span>`
    }
}

class OhLink extends DragComponent {
}

OhLink.title = "Link";
OhLink.icon = "fa fa-external-link";
OhLink.sortParams = {
    ...DragComponent.sortParams,
    useHelper: true,
    selector: ".can_drag",
    nodeTemplate: (props) => {
        return `<a href="https://odoo-studio.com" target="new">New link</a>`
    }
}

class OhGridExtend extends OhGrid {

}

OhGridExtend.sortParams = {
    ...OhGrid.sortParams,
    selector: ".oe_kanban_card, .o_kanban_record > div:not(.o_kanban_record_has_image_fill), .oe_kanban_details",
}

class OhFieldExtend extends OhField {

}

OhFieldExtend.sortParams = {
    ...OhField.sortParams,
    useHelper: true,
    selector: ".can_drag",
    nodeTemplate: (props) => {
        return `<Field name='create_uid' widget="many2one" />`;
    },
}

class OhImageExtend extends OhImage {

}
OhImageExtend.sortParams = {
    ...OhImage.sortParams,
    selector: ".can_drag",
    nodeTemplate: (props) => {
        return `<img src="/dynamic_odoo/static/img/battery_icon.png" style="width: 100%" />`;
    },
}

export const DRAG_COMPONENTS = {
    OhText,
    OhIcon,
    OhTitle,
    OhImageExtend,
    OhTags,
    OhLabel,
    OhPriority,
    OhLink,
    OhActivities,
    OhFieldExtend,
    OhGridExtend
}