/** @odoo-module **/

import {Many2OneField} from "@web/views/fields/many2one/many2one_field";

const {Component, useChildSubEnv, onWillStart, onWillUpdateProps, useState} = owl;

export class Many2oneField extends Component {
    setup() {
        super.setup();
        const {value} = this.props;
        this.state = useState({value: value});
        onWillStart(this.onWillStart);
        onWillUpdateProps(async (nextProps) => {
            if (this.state.value != nextProps.value) {
                this.state.value = await this.getValue(nextProps.value, nextProps);
            }
        });
        useChildSubEnv({inDialog: true});
    }

    async getValue(value, props) {
        const {relation, domain, value_name} = props || this.props;
        if (!value) {
            return false;
        }
        if (!Array.isArray(value)) {
            const result = await this.env.services.orm.searchRead(relation, [...(domain || []), [value_name, '=', value]], ["id", "display_name", value_name]);
            if (result.length) {
                return [result[0].id, result[0].display_name];
            }
            return [];
        }
        return value;
    }

    async onWillStart() {
        this.state.value = await this.getValue(this.props.value);
    }

    get m2oProps() {
        const {relation, canOpen, update, string, context, readonly, domain, specific_list, value_name} = this.props;
        const updateRecord = async (val) => {
            val = Object.values(val || {})?.[0];
            if (!val) {
                return;
            }
            this.state.value = val;
            if (!["id", "display_name"].includes(value_name)) {
                val = await this.env.services.orm.searchRead(relation, [["id", "=", val[0]]], specific_list ? specific_list : [value_name]);
                return update(specific_list ? val[0] : val[0][value_name]);
            }
            update(value_name == "id" ? val[0] : val[1]);
        };
        return {
            record: {
                getFieldContext: () => {
                },
                update: updateRecord.bind(this),
            },
            string: string || 'Many2one',
            name: "many2one_field",
            domain: domain,
            readonly: readonly,
            canOpen: canOpen || false,
            canQuickCreate: false,
            context: context || "{}",
            relation: relation,
            value: this.state.value,
            update: updateRecord.bind(this),
        };
    }
}

Many2oneField.template = "dynamic_odoo.Many2oneField";
Many2oneField.defaultProps = {
    value: false,
};
Many2oneField.components = {
    Many2OneField,
};
Many2oneField.props = {
    value_name: {type: String, optional: true},
    update: {type: Function, optional: true},
    value: {type: [String, Number, Array], optional: true},
    relation: {type: String, optional: true},
    domain: {type: Array, optional: true},
    canOpen: {type: Boolean, optional: true},
    specific_list: {type: Array, optional: true},
    openTarget: {type: String, optional: true}
}