/** @odoo-module **/
import {DragComponent} from "@dynamic_odoo/core/widgets/drag_component/drag_component";

class OhFilter extends DragComponent {

}

OhFilter.title = "Filter";
OhFilter.icon = "fa fa-filter";
OhFilter.sortParams = {
    ...DragComponent.sortParams,
    selector: ".items[type='filter']",
    nodeTemplate: (props) => {
        return `<filter string="New Filter" name="new_filter" domain="[]"/>`;
    },
}

class OhGroup extends DragComponent {

}

OhGroup.title = "Groups";
OhGroup.icon = "fa fa-bars";
OhGroup.sortParams = {
    ...DragComponent.sortParams,
    selector: ".items[type='groupBy']",
    nodeTemplate: (props) => {
        return `<filter string="New Group" name='new_group' context="{'group_by': 'create_uid'}" />`;
    },
}

class OhAutomation extends DragComponent {

}

OhAutomation.title = "Automation";
OhAutomation.icon = "fa fa-magic";
OhAutomation.sortParams = {
    ...DragComponent.sortParams,
    selector: ".items[type='field']",
    nodeTemplate: (props) => {
        return `<Field name='create_uid' string="New Automation" />`;
    },
}

class OhSeperator extends DragComponent {

}

OhSeperator.title = "Seperator";
OhSeperator.icon = "fa fa-pagelines";
OhSeperator.sortParams = {
    ...DragComponent.sortParams,
    selector: ".items[type='filter'], .items[type='groupBy']",
    replaceTemplate: `<div class="seperator dropdown-divider"></div>`,
    nodeTemplate: () => {
        return `<separator />`;
    },
}


export const DRAG_COMPONENTS = {
    OhFilter, OhGroup, OhAutomation, OhSeperator
}