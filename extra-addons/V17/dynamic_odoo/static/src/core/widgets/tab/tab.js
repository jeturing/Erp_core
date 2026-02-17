/** @odoo-module **/

const {Component, onMounted, onPatched, onRendered, useState} = owl;

export class Tab extends Component {
    setup() {
        super.setup();
        const {active, onChangedTab, options} = this.props;
        this.state = useState({matrix: Math.random(), active: active || Object.keys(options)[0]});
        onPatched(() => {
            if (this.changed) {
                this.changed = false;
                onChangedTab();
            }
        });
    }

    reload() {
        this.state.matrix = Math.random();
    }

    onChangeTab(tabName) {
        this.state.active = tabName;
        this.changed = true;
    }
}

Tab.template = "dynamic_odoo.Widget.Tab";
Tab.defaultProps = {
    options: {
        tab_1: {
            label: "Tab 1",
            name: "tab_1",
            view: [] // receive list (template or Component)
        },
    }
}
Tab.props = {
    options: {type: [Array, Object], optional: true},
    onChangedTab: {type: Function, optional: true}
}