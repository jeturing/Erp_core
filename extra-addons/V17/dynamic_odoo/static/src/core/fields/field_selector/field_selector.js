/** @odoo-module **/
import {ModelFieldSelector} from "@web/core/model_field_selector/model_field_selector";

const {Component} = owl;

export class FieldSelector extends Component {
    get selectorProps() {
        const {model, update, filter, value, allowEmpty, readonly, followRelations} = this.props;
        const props = {
            update: (path, info) => update({path: path, fieldInfo: info.fieldDef}),
            resModel: model,
            filter: filter,
            readonly: readonly,
            allowEmpty: allowEmpty,
            followRelations: typeof followRelations == "undefined" ? true : false,
        }
        if (value) {
            props.path = value;
        }
        return props;
    }
}

FieldSelector.template = "dynamic_odoo.FieldSelector";
FieldSelector.components = {ModelFieldSelector}
