/** @odoo-module **/

import {DomainSelectorDialog} from "@web/core/domain_selector_dialog/domain_selector_dialog";
import {useOwnedDialogs} from "@web/core/utils/hooks";

const {Component, onWillUpdateProps, useState} = owl;

export class Radio extends Component {
    setup() {
        super.setup();
        const {value, condition} = this.props;
        this.state = useState({value: this.formatValue(value), condition: this.formatCondition(condition)});
        this.addDialog = useOwnedDialogs();
        onWillUpdateProps((nextProps) => {
            const {value, condition} = this.state;
            const nextValue = this.formatValue(nextProps.value);
            const nextCondition = this.formatCondition(nextProps.condition);
            if (value != nextValue) {
                this.state.value = nextValue;
            }
            if (condition != nextCondition) {
                this.state.condition = nextCondition;
            }
        });
    }

    formatCondition(condition) {
        return typeof condition == "string" ? condition : JSON.stringify(condition || []);
    }

    formatValue(value) {
        return ["1", "True", "true", true, 1].includes(value);
    }

    onUpdate(val, isCondition = false) {
        const stateName = isCondition ? 'condition' : 'value';
        this.state[stateName] = val;
        this.props.update(this.props.useCondition ? {value: val, isCondition: isCondition} : val);
    }

    showCondition() {
        const {condition} = this.state, {model} = this.props;
        this.addDialog(DomainSelectorDialog, {
            resModel: model,
            domain: condition,
            // domain: '[("state", "=", "draft")]',
            readonly: false,
            isDebugMode: true,
            onConfirm: (val) => this.onUpdate(val, true),
        });
    }

    getClass() {
        const {value, condition} = this.state, classes = ["radio_field"];
        if (condition.length > 2) {
            classes.push("has_condition");
        }
        if (value) {
            classes.push("checked")
        }
        return classes.join(" ")
    }
}

Radio.noFieldLabel = true;
Radio.template = "dynamic_odoo.Field.Radio";
Radio.props = {
    label: {type: String, optional: true},
    model: {type: String, optional: true},
    value: {type: [Boolean, String], optional: true},
    readonly: {type: Boolean, optional: true},
    update: {type: Function, optional: true},
    useCondition: {type: Boolean, optional: true},
    condition: {type: [String, Array], optional: true}
}