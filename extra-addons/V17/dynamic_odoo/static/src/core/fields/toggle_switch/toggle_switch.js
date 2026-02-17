/** @odoo-module **/

const {Component, useRef, useState, onWillUpdateProps, onMounted, onWillUnmount} = owl;

export class ToggleSwitch extends Component {
    setup() {
        super.setup();
        const {value} = this.props;
        this.state = useState({value: this.formatValue(value)});
        onWillUpdateProps((nextProps) => {
            if (nextProps.hasOwnProperty("value")) {
                this.state.value = this.formatValue(nextProps.value);
            }
        });
    }

    formatValue(value) {
        return ["1", "True", "true", true, 1].includes(value);
    }

    onChangeInput() {
        this.state.value = !this.state.value;
        this.props.update(this.state.value);
    }
}

ToggleSwitch.noFieldLabel = true;
ToggleSwitch.template = "dynamic_odoo.Field.ToggleSwitch";
