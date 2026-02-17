/** @odoo-module **/
import {CharField, IntegerField} from "@dynamic_odoo/core/fields/char_field/char_field"
import {SelectionField} from "@dynamic_odoo/core/fields/selection_field/selection_field";
import {Many2oneField} from "@dynamic_odoo/core/fields/many2one_field/many2one_field";
import {ToggleSwitch} from "@dynamic_odoo/core/fields/toggle_switch/toggle_switch";
import {StudioDateTimeField} from "@dynamic_odoo/core/fields/datetime_field/datetime_field";

const {Component, onWillUpdateProps, onWillStart} = owl;

export class DefaultFieldValue extends Component {
    setup() {
        onWillStart(async () => {
            await this.loadData();
        });
        onWillUpdateProps(async (nextProps) => {
            await this.loadData(nextProps);
        });
    }

    get prepareField() {
        const sampleProps = (component, wrap = false, props = {}) => {
            return {
                component: component,
                formatValue: (value) => wrap ? `"${value}"` : value,
                props: () => ({...props})
            }
        }
        const {field} = this.props, fieldSupported = {
            selection: sampleProps(SelectionField, true, {options: field.selection}),
            char: sampleProps(CharField, true, {classes: "input_base"}),
            text: sampleProps(CharField, true, {classes: "input_base"}),
            integer: sampleProps(IntegerField, false, {classes: "input_base"}),
            float: sampleProps(IntegerField, false, {classes: "input_base"}),
            many2one: sampleProps(Many2oneField, false, {relation: field.relation, value_name: "id"}),
            boolean: {
                component: ToggleSwitch,
                formatValue: (value) => `"${value ? 'True' : 'False'}"`,
                props: () => ({hideLabel: true})
            },
            datetime: sampleProps(StudioDateTimeField, true, {type: "datetime"}),
            date: sampleProps(StudioDateTimeField, true, {type: "date"}),
        }
        return fieldSupported[field.type in fieldSupported ? field.type : "char"];
    }

    async loadData(props = this.props) {
        const {name, value, model} = props;
        let json_value = value;
        if (!value) {
            const field_value = await this.env.services.orm.searchRead("ir.default", [['field_id.name', '=', name], ['field_id.model_id.model', '=', model]], []);
            if (field_value.length) {
                json_value = field_value[0].json_value;
            }
        }
        this.json_value = json_value ? JSON.parse(json_value) : json_value;
    }
}

DefaultFieldValue.template = "dynamic_odoo.DefaultFieldValue";
DefaultFieldValue.components = {CharField}