/** @odoo-module **/

import {useService} from "@web/core/utils/hooks";
import {FormViewDialog} from "@web/views/view_dialogs/form_view_dialog";

const {Component} = owl;

export class MoreField extends Component {
    setup() {
        super.setup();
        this.dialogService = useService("dialog");
    }

    async getFieldID() {
        const domain = this.props.domain(this.props)
        if (domain.length) {
            const record = await this.env.services.orm.searchRead(this.props.resModel, domain, ["id"]);
            return record[0].id;
        }
        return null;
    }

    async onShowMore() {
        const {title, resModel} = this.props;
        const resId = await this.getFieldID()
        this.dialogService.add(FormViewDialog, {
            title: title,
            context: {},
            resId: resId,
            resModel: resModel,
            onRecordSaved: (record) => {
                this.props.update();
            },
        });
    }
}

MoreField.noFieldLabel = true;
MoreField.template = "dynamic_odoo.Field.More";
MoreField.defaultProps = {
    remove: true,
    title: "Change Field Property",
    resModel: "ir.model.fields",
    domain: (props) => {
        const {value} = props;
        if (typeof value == "string") {
            return [['model', '=', odoo.studio.getState().model], ["name", "=", value]];
        }
        return [];
    }
};
MoreField.props = {
    title: {type: String, optional: true},
    domain: {type: [Array, Function], optional: true},
    resModel: {type: String, optional: true},
    remove: {type: Boolean, optional: true},
    more: {type: Boolean, optional: true},
    value: {type: [Number, String], optional: true},
    label: {type: String, optional: true},
    update: {type: Function, optional: true},
    onRemove: {type: Function, optional: true},
}