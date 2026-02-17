/** @odoo-module **/
import {Field} from "@dynamic_odoo/core/fields/field";

const {Component} = owl;

export class FieldOptionsWidget extends Component {

    get prepareFields() {
        const {options, value} = this.props,
            fieldType = (type) => ({boolean: "radio", string: "char", array: "selection"}[type] || type);

        return Object.keys(options || {}).map((optionName) => {
            const option = options[optionName];
            const fieldProps = {
                type: fieldType(option.type), label: option.string, description: option.description, props: {
                    update: (value) => this.props.update({name: optionName, value: value})
                }
            }
            if (option.type == "array") {
                const {params, default_value} = option;
                fieldProps.props.options = params.params.map((param) => [param.field_name, param.label]);
                if (default_value) {
                    fieldProps.props.multiple = true;
                    fieldProps.props.value = default_value;
                }
            }
            if (option.type == "selection") {
                fieldProps.props.options = option.params.selection;
            }
            if (optionName in (value || {})) {
                fieldProps.props.value = value[optionName];
            }
            return fieldProps;
        });
    }
}

FieldOptionsWidget.template = "dynamic_odoo.Report.FieldOptionWidget";
FieldOptionsWidget.components = {Field};