/** @odoo-module **/

import {Dialog} from "@web/core/dialog/dialog";
import {useOwnedDialogs} from "@web/core/utils/hooks";

const {Component, xml, useRef, useState} = owl;

class OptionsCenter extends Component {
    setup() {
        super.setup();
        this.state = useState({items: this.props.items, itemEdit: false});
        this.inputRef = useRef("input");
        this.inputUpdateRef = useRef("inputUpdate");
    }

    onRemove(itemName) {
        const {items} = this.state;
        items.splice(items.findIndex((item) => item.name == itemName), 1);
    }

    onUpdate(itemName) {
        const {items} = this.state;
        items[items.findIndex((item) => item.name == itemName)] = this.itemByRef(this.inputUpdateRef);
    }

    // onPick (name) {
    //     const {picked} = this.state;
    //     if (!picked.includes(name)) {
    //         return this.state.picked.push(name);
    //     }
    //     picked.splice(picked.indexOf(name), 1);
    // }
    onAdd() {
        this.state.items.push(this.itemByRef(this.inputRef));
        this.inputRef.el.value = "";
    }

    itemByRef(inputRef) {
        const label = inputRef.el.value;
        return {name: label.toLowerCase().replaceAll(" ", "_"), string: label};
    }
}

OptionsCenter.template = "dynamic_odoo.Field.OptionsCenterDialog";
OptionsCenter.components = {Dialog}
OptionsCenter.props = {
    title: {type: String, optional: true},
    placeholder: {type: String, optional: true},
    update: {type: Function, optional: true},
    close: {type: Function, optional: true},
    items: {type: Array, optional: true},
    canCreate: {type: Boolean, optional: true},
    usePicked: {type: Boolean, optional: true}
}
OptionsCenter.defaultProps = {
    title: "Create a option for Selection",
    placeholder: "Create a new option",
    canCreate: true,
}

export class SelectionOptions extends Component {
    setup() {
        super.setup();
        this.addDialog = useOwnedDialogs();
    }

    showOptionsCenter() {
        const {canCreate, usePicked, options, update} = this.props;
        this.addDialog(OptionsCenter, {
            canCreate: canCreate,
            usePicked: usePicked || false,
            items: options || [],
            update: (val) => update(val),
        });
    }
}

SelectionOptions.template = "dynamic_odoo.Field.OptionsCenter";
