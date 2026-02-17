/** @odoo-module **/

const {Component, useRef, useState} = owl;

export class SelectionField extends Component {
    setup() {
        super.setup();
        const {value, multiple} = this.props;
        this.state = useState({value: multiple ? (value || []) : value});
        this.select = useRef("select");
    }

    isVisible(data) {
        const {value} = this.state;
        return this.props.multiple ? !(value || []).includes(data) : true;
    }

    onCloseTag(data) {
        this.state.value = this.props.multiple ? this.state.value.filter((val) => val != data) : undefined;
        this.props.update(this.state.value);
    }

    getLabel(data) {
        const option = this.props.options.filter((op) => op[0] == data);
        if (option.length) return option[0][1];
        return [data.substr(0, 1).toUpperCase(), data.substring(1)].join("");
    }

    onChange(data) {
        this.props.multiple ? this.state.value.push(data) : (this.state.value = data);
        this.props.update(this.state.value);
    }

    // onMounted() {
    //     // this.changeListenerCallback = this.changeListenerCallback.bind(this);
    //     // this.select.el.addEventListener('change', this.changeListenerCallback);
    // }
    //
    // onWillUnmount() {
    //     // this.select.el.removeEventListener('change', this.changeListenerCallback);
    // }
    //
    // async changeListenerCallback(ev) {
    //     this.state.value = ev.target.value;
    //     this.props.update(ev.target.value);
    // }
}

SelectionField.template = "dynamic_odoo.SelectionField";
SelectionField.defaultProps = {};
SelectionField.props = {
    options: {type: Array},
    value: {type: [String, Array], optional: true},
    update: {type: Function, optional: true},
    multiple: {type: Boolean, optional: true},
};
