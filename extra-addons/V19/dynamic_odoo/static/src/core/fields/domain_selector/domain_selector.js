/** @odoo-module **/

import {DomainSelectorDialog} from "@web/core/domain_selector_dialog/domain_selector_dialog";
import {useOwnedDialogs} from "@web/core/utils/hooks";

const {Component, onWillUpdateProps, useState} = owl;

class DomainSelectorDialogExtend extends DomainSelectorDialog {
    static props = {
        ...DomainSelectorDialog.props,
        isDynamicModel: {type: Boolean, optional: true}
    };

    async onConfirm() {
        if (!this.props.isDynamicModel) {
            return super.onConfirm();
        }
        this.props.onConfirm(this.state.domain);
        this.props.close();
    }
}

export class DomainSelector extends Component {
    setup() {
        super.setup();
        const {value} = this.props;
        this.state = useState({value: value || "[]"});
        this.addDialog = useOwnedDialogs();
        onWillUpdateProps((nextProps) => {
            this.state.value = nextProps.value;
        });
    }

    showDomainDialog() {
        this.addDialog(DomainSelectorDialogExtend, {
            resModel: this.props.model,
            domain: this.state.value || "[]",
            readonly: false,
            isDynamicModel: this.props.isDynamicModel,
            isDebugMode: true,
            onConfirm: (val) => {
                this.state.value = val;
                this.props.update(val);
            },
        });
    }
}

DomainSelector.template = "dynamic_odoo.Widget.DomainSelector";
