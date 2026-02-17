/** @odoo-module **/

import {TextField} from "@web/views/fields/text/text_field";
import {HtmlField, htmlField} from "@web_editor/js/backend/html_field";

const {Component} = owl;

export class StudioHtmlField extends Component {
    get htmlProps() {
        const {value, update} = this.props;
        const extractProps = htmlField.extractProps({attrs: {}, options: {}}, {});
        return {
            ...extractProps,
            name: "html_field",
            record: {
                fields: {html_field: {}},
                update: (value) => update(value.html_field),
                resModel: false,
                data: {html_field: value},
                model: {bus: this.env.bus},
                resId: false
            },
        };
    }
}

StudioHtmlField.template = "dynamic_odoo.TextField";
StudioHtmlField.components = {HtmlField};
