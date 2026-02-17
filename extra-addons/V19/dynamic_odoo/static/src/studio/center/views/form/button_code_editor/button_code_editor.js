/** @odoo-module **/
import {CodeEditor} from "@web/core/code_editor/code_editor";

const {Component, onWillStart} = owl;

export class ButtonCodeEditor extends Component {
    setup() {
        super.setup();
        onWillStart(async () => {
            await this.loadButtonData();
        });
    }

    async loadButtonData() {
        const {btn_key} = this.props;
        const records = await this.env.services.orm.searchRead("studio.button", [['btn_key', '=', btn_key]], ["id", "python_code", "btn_key"]);
        this.buttonData = records.length ? records[0] : {id: false, btn_key: btn_key, python_code: ""};
    }

    handleChange(editedValue) {
        this.buttonData.python_code = editedValue;
        this.props.update(this.buttonData);
    }
}

ButtonCodeEditor.template = "dynamic_odoo.ButtonCodeEditor";
ButtonCodeEditor.components = {CodeEditor}
