/** @odoo-module **/

import {Field} from "@dynamic_odoo/core/fields/field";
import {dispatchEvent} from "@dynamic_odoo/core/studio_core";
import {useOwnedDialogs} from "@web/core/utils/hooks";
import {DomainSelectorDialog} from "@web/core/domain_selector_dialog/domain_selector_dialog";

const {Component, onWillStart, onWillUpdateProps, useState} = owl;

export const approvalCache = {
    cache: {},
    get: (btn_key) => {
        return approvalCache.cache[btn_key]
    },
    set: (btn_key, data) => {
        approvalCache.cache[btn_key] = data;
    },
    clear: () => {
        approvalCache.cache = {};
    }
}

export class Approval extends Component {
    setup() {
        super.setup();
        this.state = useState({rules: []});
        this.addDialog = useOwnedDialogs();
        this.env.bus.addEventListener("APPROVAL:CLEAR", () => {
            approvalCache.clear();
        });
        onWillStart(async () => {
            this.state.rules = await this.loadRules(this.props.key);
        });
        onWillUpdateProps(async (nextProps) => {
            if (this.props.key != nextProps.key) {
                this.state.rules = await this.loadRules(nextProps.key);
            }
        });
    }

    async loadRules(btn_key) {
        let rules = approvalCache.get(btn_key) || [];
        if (!rules.length) {
            const result = await this.env.services.orm.searchRead("studio.approval.rules",
                [['btn_id.btn_key', '=', btn_key]],
                ['allowed_group', 'responsible', 'users_to_notify', 'description', 'exclusive_approval', 'notification_order', 'filter'], {order: "notification_order"});
            if (result.length) {
                rules = result.map((approval) => ({data_exist: {...approval}, data: {id: approval.id}}));
                approvalCache.set(btn_key, rules);
                rules[0].active = true;
            }
        }
        return rules;
    }

    makeFields(rule) {
        const ruleData = {...rule.data_exist, ...rule.data};
        const fields = {
            allowed_group: {
                type: "many2one",
                label: "Allowed Group",
                props: {relation: "res.groups", value_name: "id"}
            },
            responsible: {
                type: "many2one",
                label: "Responsible",
                props: {
                    relation: "res.users",
                    value_name: "id",
                    domain: ruleData.allowed_group ? [['groups_id', 'in', [ruleData.allowed_group[0]]]] : []
                }
            },
            users_to_notify: {
                type: "many2many",
                label: "Users to notify",
                // relation: "ir.model.fields", value_name: "name", value: value,
                // domain: [["store", "=", true], ["ttype", "in", types], ["name", "!=", "id"], ["model", "=", model]],
                props: {relation: "res.users", value_name: "id"}
            },
            description: {type: "char", label: "Description", props: {}},
            exclusive_approval: {type: "radio", label: "Exclusive approval", props: {}},
            notification_order: {type: "integer", label: "Notification order", props: {}}
        }
        Object.keys(fields).map((fieldName) => {
            const field = fields[fieldName];
            field.name = fieldName;
            field.props.update = (value) => {
                rule.data[field.name] = value;
                this.dispatchAPPROVAL.bind(this)();
            };
            if (fieldName in ruleData) {
                const fieldValue = ruleData[fieldName];
                field.props.value = Array.isArray(fieldValue) ? [...fieldValue] : fieldValue;
            }
        });
        return fields;
    }

    dataToSave() {
        const {rules} = this.state, data = {new: [], update: [], delete: []};
        rules.filter((rule) => !(rule.type == "delete" && rule.isNew)).map((rule) => {
            data[rule.type || "update"].push(rule.data);
        });
        return data;
    }

    dispatchAPPROVAL() {
        const model = this.props.model || (odoo.studio && odoo.studio.getState().model);
        dispatchEvent("STUDIO_FORM:APPROVAL_UPDATE", {
            approval: {
                key: this.props.key,
                btn_string: this.props.btn_string,
                model: model,
                rules: this.dataToSave()
            }
        }, this.__owl__.bdom.el);
    }

    onDelete(rule) {
        rule.type = 'delete';
        // rule.data.id = rule.data_exist?.id;
        this.dispatchAPPROVAL();
        this.props.update(this.state.rules.length);
    }

    onShowFilter(rule) {
        this.addDialog(DomainSelectorDialog, {
            resModel: this.props.model,
            domain: rule.data?.filter || rule.data_exist?.filter || "[]",
            readonly: false,
            isDebugMode: true,
            onConfirm: (val) => {
                rule.data.filter = val;
                this.dispatchAPPROVAL();
            },
        });
    }

    newApprovalRule() {
        this.state.rules.map((rule) => (rule.active = false));
        this.state.rules.push({active: true, isNew: true, type: "new", data: {}});
        approvalCache.set(this.props.key, this.state.rules);
        this.props.update(this.state.rules.length);
    }

}

Approval.noFieldLabel = true;
Approval.template = "dynamic_odoo.Field.Approval";
Approval.components = {Field}