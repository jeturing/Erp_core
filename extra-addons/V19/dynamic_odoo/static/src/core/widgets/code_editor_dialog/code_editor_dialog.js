/** @odoo-module **/
import {Dialog} from "@web/core/dialog/dialog";
import {CodeEditor} from "@web/core/code_editor/code_editor";

const {Component} = owl;

export class CodeEditorDialog extends Component {

    handleChange(editedValue) {
        this.editedValue = editedValue;
    }

    onUpdate() {
        this.props.update(this.editedValue);
        this.props.close();
    }
}

CodeEditorDialog.template = "dynamic_odoo.CodeEditorDialog";
CodeEditorDialog.components = {CodeEditor, Dialog}
