/** @odoo-module **/

import {DomainSelectorDialog} from "@web/core/domain_selector_dialog/domain_selector_dialog";
import {useOwnedDialogs} from "@web/core/utils/hooks";

const {Component, useState} = owl;

export class RecordColor extends Component {
    setup() {
        super.setup();
        const {value} = this.props;
        this.state = useState({value: value || {}});
        this.addDialog = useOwnedDialogs();
    }

    get decorations() {
        return {
            "decoration-danger": {}, "decoration-warning": {},
            "decoration-success": {}, "decoration-primary": {}, "decoration-info": {},
            "decoration-muted": {}, "decoration-bf": {placeholder: "Bold"},
            "decoration-it": {placeholder: "Italic"}
        };
    }

    showCondition(decorationName) {
        this.addDialog(DomainSelectorDialog, {
            resModel: this.props.model,
            domain: this.state.value[decorationName] || "[]",
            readonly: false,
            isDebugMode: true,
            onConfirm: (val) => {
                this.state.value[decorationName] = val;
                this.props.update(this.state.value);
            },
        });
    }
}

RecordColor.noFieldLabel = true;
RecordColor.template = "dynamic_odoo.Widget.DecorationColor";
RecordColor.defaultProps = {
    model: (odoo.studio && odoo.studio.getState().model),
};
RecordColor.props = {
    label: {type: String, optional: true},
    model: {type: String, optional: true},
    value: {type: [Boolean, String, Object, Array], optional: true},
    update: {type: Function, optional: true},
}
