/** @odoo-module **/
import {CodeEditor} from "@web/core/code_editor/code_editor";

const {Component} = owl;

export class StudioCodeEditor extends Component {

    handleChange(editedValue) {
        this.editedValue = editedValue;
    }

    onUpdate() {
        this.props.update(this.editedValue);
        this.props.close();
    }
}

StudioCodeEditor.template = "dynamic_odoo.CodeEditor";
StudioCodeEditor.components = {CodeEditor}
