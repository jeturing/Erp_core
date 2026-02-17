/** @odoo-module **/

const {Component, useRef, useState, onWillUpdateProps, onMounted, onWillUnmount} = owl;

export class CharField extends Component {
    setup() {
        const self = this, {value} = this.props;
        this.state = useState({value: typeof value == "undefined" ? "" : value});
        this.input = useRef("input");
        onMounted(this.onMounted);
        onWillUnmount(this.onWillUnmount);
        onWillUpdateProps(async (nextProps) => {
            if (self.props.value != nextProps.value) {
                self.state.value = nextProps.value;
            }
        });
    }

    getValue() {

    }

    async keyupListenerCallback(ev) {
        ev.stopPropagation();
        ev.stopImmediatePropagation();
        this.state.value = ev.target.value;
        const {update, clear} = this.props;
        if (update) {
            update(this.state.value);
            if (clear) {
                this.state.value = '';
            }
        }
    }

    onMounted() {
        this.keyupListenerCallback = this.keyupListenerCallback.bind(this);
        this.input.el.addEventListener(this.props.useKeyUp ? "keyup" : 'change', this.keyupListenerCallback);
    }

    onWillUnmount() {
        this.input.el.removeEventListener(this.props.useKeyUp ? "keyup" : 'change', this.keyupListenerCallback);
    }

    get formattedValue() {
        // const {type} = this.props;
        // if (type == "char") {
        //     return formatChar(this.state.value, {isPassword: this.props.isPassword});
        // } else if (type == "integer") {
        //     return formatInteger(this.state.value);
        // }
        return this.state.value;
    }

    parse(value) {
        if (this.props.shouldTrim) {
            return value.trim();
        }
        return value;
    }
}

CharField.template = "dynamic_odoo.CharField";
CharField.defaultProps = {
    type: "text",
};
CharField.props = {
    type: {type: String, optional: true},
    classes: {type: String, optional: true},
    autocomplete: {type: String, optional: true},
    update: {type: Function, optional: true},
    value: {type: [String, Number], optional: true},
    isPassword: {type: Boolean, optional: true},
    placeholder: {type: String, optional: true},
    shouldTrim: {type: Boolean, optional: true},
    maxLength: {type: Number, optional: true},
    clear: {type: Boolean, optional: true},
    useKeyUp: {type: Boolean, optional: true},
};


export class IntegerField extends CharField {
}

IntegerField.defaultProps = {
    type: "number",
}