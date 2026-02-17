/** @odoo-module **/

import {CharField} from "@dynamic_odoo/core/fields/char_field/char_field";
const {Component} = owl;

export class ListString extends Component {
    onUpdate(index, data) {
        this.props.update(data);
    }
}

ListString.template = "dynamic_odoo.Widget.ListString";
ListString.components = {CharField};

