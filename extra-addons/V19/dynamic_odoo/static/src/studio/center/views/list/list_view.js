/** @odoo-module **/

import {registry} from "@web/core/registry";
import {ListController} from "@web/views/list/list_controller";
import {ListArchParser} from "@web/views/list/list_arch_parser";
import {ListRenderer} from "@web/views/list/list_renderer";
import {RelationalModel} from "@web/model/relational_model/relational_model";
import {listView} from "@web/views/list/list_view";
import {evaluateExpr} from "@web/core/py_js/py";
import {archParseBoolean} from "@web/views/utils";
import {viewStudioProps} from "@dynamic_odoo/studio/center/view_components";
import {dispatchEvent} from "@dynamic_odoo/core/studio_core";

const studioViewRegistry = registry.category("studio_views");
const {onWillUpdateProps, useEffect} = owl;


class StudioListArchParser extends ListArchParser {
    parseFieldNode(node, models, modelName) {
        const fieldNode = super.parseFieldNode(node, models, modelName);
        if (this.showAllInvisible) {
            fieldNode.original_invisible = fieldNode.column_invisible;
            fieldNode.attrs.column_invisible = "False";
            fieldNode.column_invisible = "False";
        }
        return fieldNode;
    }

    parse(xmlDoc, models, modelName) {
        this.showAllInvisible = archParseBoolean(xmlDoc.getAttribute("show_all_invisible"));
        const parseInfo = super.parse(xmlDoc, models, modelName);
        parseInfo.showAllInvisible = this.showAllInvisible;
        return parseInfo;
    }
}

class StudioListModel extends RelationalModel {
    // static Record = StudioRecord;
    setup(params, state) {
        this.params = params;
        super.setup(params, state);
    }

    _createRoot(config, data) {
        const {parent} = this.params;
        if (parent) {
            config.context.parent = parent;
        }
        return super._createRoot(config, data);
    }
}

class StudioListRenderer extends ListRenderer {
    setup() {
        super.setup();
        onWillUpdateProps((nextProps) => {
            this.allColumns.map((column) => {
                column.id = `column_${Math.random()}`;
            });
        });
        useEffect(() => {
            dispatchEvent("MODIFIER:PATCHED");
        });
    }

    get treeNodeId() {
        return this.props.archInfo.xmlDoc.getAttribute('node-id')
    }

    getActiveFields(list) {
        const {showAllInvisible} = this.props.archInfo, {activeFields} = list;
        return [...(new Set(Object.keys(activeFields).filter((fieldName) => showAllInvisible || !evaluateExpr(activeFields[fieldName].invisible))))]
    }

    getColumnClass(column) {
        const classes = super.getColumnClass(column);
        if (this.evalColumnInvisible(column.original_invisible)) {
            return `${classes} column_invisible`;
        }
        return classes;
    }

    getCellClass(column, record) {
        const classes = super.getCellClass(column, record);
        if (this.evalColumnInvisible(column.original_invisible)) {
            return `${classes} column_invisible`;
        }
        return classes;
    }

    isSortable(column) {
        return false;
    }
}

StudioListRenderer.rowsTemplate = "dynamic_odoo.ListRenderer.Rows";
StudioListRenderer.template = "dynamic_odoo.ListRenderer";

class StudioListController extends ListController {
    setup() {
        super.setup();
        onWillUpdateProps((nextProps) => {
            this.archInfo = nextProps.archInfo;
        });
    }

    get modelParams() {
        const modelParams = super.modelParams;
        const {parent, limit} = this.props;
        if (parent) {
            modelParams.parent = parent;
        }
        modelParams.limit = limit;
        return modelParams;
    }
}

StudioListController.template = "dynamic_odoo.ListView";
StudioListController.props = {
    ...ListController.props,
    ...viewStudioProps,
}

export const studioListView = {
    ...listView,
    ArchParser: StudioListArchParser,
    Model: StudioListModel,
    Renderer: StudioListRenderer,
    Controller: StudioListController
};

studioViewRegistry.add("list_studio", studioListView);


