/** @odoo-module **/

import {registry} from "@web/core/registry";
import {KanbanController} from "@web/views/kanban/kanban_controller";
import {KanbanRenderer} from "@web/views/kanban/kanban_renderer";
import {KanbanCompiler} from "@web/views/kanban/kanban_compiler";
import {kanbanView} from "@web/views/kanban/kanban_view";
import {KanbanRecord} from "@web/views/kanban/kanban_record";
import {dispatchEvent} from "@dynamic_odoo/core/studio_core";
import {extractFieldsFromArchInfo} from "@web/model/relational_model/utils";
import {viewStudioProps} from "@dynamic_odoo/studio/center/view_components";
import {makeWrapper, WrapComponent} from "../wrap_node_compiled";

const studioViewRegistry = registry.category("studio_views");
const {onWillUpdateProps, useEffect} = owl;

export class StudioKanbanCompiler extends KanbanCompiler {
    compileField(el, params) {
        const compiled = super.compileField(el, params), nodeId = el.getAttribute("node-id");
        if (nodeId) {
            if (compiled.tagName == "Field") {
                return makeWrapper(el, compiled, nodeId)
            } else if (el.tagName == "field") {
                compiled.setAttribute("node-id", nodeId);
            }
        }
        return compiled;
    }
}

class StudioKanbanRecord extends KanbanRecord {
}

StudioKanbanRecord.components = {...StudioKanbanRecord.components, WrapComponent}
StudioKanbanRecord.Compiler = StudioKanbanCompiler;


class StudioKanbanController extends KanbanController {
    setup() {
        onWillUpdateProps((nextProps) => {
            const {activeFields, fields} = extractFieldsFromArchInfo(nextProps.archInfo, nextProps.fields);
            this.model.root.config.fields = fields;
            this.model.root.config.activeFields = activeFields;
        });
        super.setup();
    }
}

StudioKanbanController.template = "dynamic_odoo.KanbanView";
StudioKanbanController.props = {
    ...KanbanController.props,
    ...viewStudioProps,
}

class StudioKanbanRenderer extends KanbanRenderer {
    static components = {
        ...StudioKanbanRenderer.components,
        KanbanRecord: StudioKanbanRecord
    };

    setup() {
        super.setup();
        onWillUpdateProps((nextProps) => {
            const {activeFields} = extractFieldsFromArchInfo(nextProps.archInfo, nextProps.list.config.fields);
            nextProps.list.config.activeFields = activeFields;
        });
        useEffect(() => {
            const firstNode = this.__owl__.bdom.firstNode();
            ["o_form_uri", "o-mail-ActivityButton", "oe_kanban_action"].map((cl) => {
                const resultNodes = firstNode.getElementsByClassName(cl);
                for (let i = 0; i < resultNodes.length; i++) {
                    const itemNode = resultNodes[i];
                    if (itemNode.tagName.toLowerCase() == "a") {
                        itemNode.removeAttribute("href");
                    }
                    itemNode.replaceWith(itemNode.cloneNode(true));
                }
            })
            dispatchEvent("MODIFIER:PATCHED");
        });
    }
}


export const studioKanbanView = {
    ...kanbanView,
    Compiler: StudioKanbanCompiler,
    Renderer: StudioKanbanRenderer,
    Controller: StudioKanbanController
};
studioViewRegistry.add("kanban_studio", studioKanbanView);


