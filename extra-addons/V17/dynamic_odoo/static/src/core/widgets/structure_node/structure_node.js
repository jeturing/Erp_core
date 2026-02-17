/** @odoo-module **/

import {Field} from "@dynamic_odoo/core/fields/field";
import {CodeEditor} from "@web/core/code_editor/code_editor";
import {stringToJson, jsonNodeToString} from "@dynamic_odoo/core/utils/view";
import {useOwnedDialogs} from "@web/core/utils/hooks";
import {CodeEditorDialog} from "@dynamic_odoo/core/widgets/code_editor_dialog/code_editor_dialog";

const {Component, onWillUpdateProps, useState} = owl;


export class StructureNode extends Component {
    setup() {
        super.setup();
        this.addDialog = useOwnedDialogs();
    }

    getAttrsShow(node) {
        const result = [];
        ["class", "t-name", "t-call", "t-set", "t-value"].map((attr) => {
            const val = node.attrs[attr];
            if (val) {
                result.push(attr + ":" + val);
            }
        });
        return result.length ? "[" + result.join(",") + "]" : '';
    }

    get structureNodeString() {
        const {structureNode, viewInfo} = this.props;
        return jsonNodeToString(structureNode || viewInfo.archJson);
    }

    getStructure() {
        const {node, structureNode, viewInfo} = this.props, nodeStructure = [];
        if (!node) {
            return nodeStructure;
        }
        const _loopChild = (_node, fn = () => {
        }) => {
            if (_node.nodeId == node.nodeId) {
                fn();
                nodeStructure.push(_node);
            }
            (_node.children || []).filter((child) => {
                _loopChild(child, () => {
                    fn();
                    nodeStructure.push(_node)
                });
            });
        }

        _loopChild(structureNode || viewInfo.archJson);
        return nodeStructure;
    }

    getNodeModifier() {
        const {nodeModifier, viewInfo, reload, node} = this.props;
        return new nodeModifier(node, {
            viewInfo: viewInfo,
            app: this.__owl__.app,
            onNodeChangeProp: (prop, value) => reload()
        });
    }

    onShowCodeEdit() {
        this.addDialog(CodeEditorDialog, {
            value: this.structureNodeString,
            update: (val) => this.props.onSaveCode(val),
        });
    }
}

StructureNode.template = "dynamic_odoo.widgets.structure_node";
StructureNode.components = {Field, CodeEditor}
