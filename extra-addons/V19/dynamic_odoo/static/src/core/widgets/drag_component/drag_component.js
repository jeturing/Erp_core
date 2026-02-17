/** @odoo-module **/

const {Component, useEffect, onWillPatch, useState, onMounted} = owl;

export class DragComponent extends Component {
    setup() {
        super.setup();
        useEffect(() => {
            const el = this.__owl__.bdom.el, $el = $(el), key = Math.random().toString().replace("0.", "DC_");
            this.key = key;
            this.el = el;
            $el.attr("key", key).data("component", this);
            $el.find(".drag_com").data("component", this);
        });
        this.state = useState({matrix: false});
    }

    forceUpdate() {
        this.render(true);
    }
}

DragComponent.title = "Component";
DragComponent.icon = "fa fa-plus";
DragComponent.template = "dynamic_odoo.DragComponent";
DragComponent.sortParams = {
    isNew: true,
}

export class OhField extends DragComponent {
}

OhField.title = "Field";
OhField.icon = "fa fa-foursquare";
OhField.replaceClass = "rp_field";
OhField.sortParams = {
    ...DragComponent.sortParams,
    selector: ".container, div[class*='col-'], .col, .can_drag",
    nodeTemplate: (props) => {
        return "<field name='" + props.name + "' />"
    },
    replaceClass: "rp_field"
}

export class OhGrid extends DragComponent {
}

OhGrid.title = "Grid";
OhGrid.icon = "fa fa-object-group";
OhGrid.sortParams = {
    ...DragComponent.sortParams,
    useHelper: true,
    selector: ".container, div[class*='col-'], .col, .can_drag",
    nodeTemplate: "dynamic_odoo.DragComponent.Grid",
    replaceTemplate: "dynamic_odoo.DragComponent.Grid",
    replaceClass: "rp_grid"
}

export class OhTitle extends DragComponent {
}

OhTitle.title = "Title";
OhTitle.icon = "fa fa-shield";
OhTitle.sortParams = {
    ...DragComponent.sortParams,
    useHelper: true,
    selector: ".container, div[class*='col-'], .col, .can_drag",
    nodeTemplate: "dynamic_odoo.DragComponent.Title",
    replaceClass: "rp_title"
}

export class OhIcon extends DragComponent {
}

OhIcon.title = "Icon";
OhIcon.icon = "fa fa-hand-spock-o";
OhIcon.sortParams = {
    ...DragComponent.sortParams,
    useHelper: true,
    selector: ".container, div[class*='col-'], .col, .can_drag",
    nodeTemplate: "dynamic_odoo.DragComponent.Icon",
    replaceTemplate: "dynamic_odoo.DragComponent.Icon",
    replaceClass: "rp_icon",
    helperClass: "helper_inline",
}

export class OhImage extends DragComponent {
}

OhImage.title = "Image";
OhImage.icon = "fa fa-picture-o";
OhImage.sortParams = {
    ...DragComponent.sortParams,
    useHelper: true,
    selector: ".container, div[class*='col-'], .col, .can_drag",
    nodeTemplate: "dynamic_odoo.DragComponent.Image",
    replaceClass: "rp_image"
}

export class OhData extends DragComponent {
}

OhData.title = "Data";
OhData.icon = "fa fa-asterisk";
OhData.sortParams = {
    ...DragComponent.sortParams,
    useHelper: true,
    selector: ".container, div[class*='col-'], .col, .can_drag",
    nodeTemplate: "dynamic_odoo.DragComponent.Data",
    replaceClass: "rp_data"
}

export class OhLink extends DragComponent {
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

export class OhText extends DragComponent {
}

OhText.title = "Text";
OhText.icon = "fa fa-text-width";
OhText.sortParams = {
    ...DragComponent.sortParams,
    useHelper: true,
    selector: ".container, div[class*='col-'], .col, .can_drag",
    replaceTemplate: "<span>New Text</span>",
    nodeTemplate: (props) => {
        return `<span>New Text</span>`
    }
}
