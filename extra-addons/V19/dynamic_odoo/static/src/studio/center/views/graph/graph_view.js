/** @odoo-module **/

import {registry} from "@web/core/registry";
import {GraphController} from "@web/views/graph/graph_controller";
import {GraphModel} from "@web/views/graph/graph_model";
import {graphView} from "@web/views/graph/graph_view";
import {viewStudioProps} from "@dynamic_odoo/studio/center/view_components";

const studioViewRegistry = registry.category("studio_views");
const {onWillUpdateProps} = owl;

class StudioGraphModel extends GraphModel {
    setup(params) {
        super.setup(params);
        onWillUpdateProps(async (nextProps) => {
            const {context, modelParams} = nextProps;
            if (context.Studio) {
                const {measure, mode, fields, resModel, stacked, area, smooth, groupBy} = modelParams;
                this.metaData.groupBy = groupBy;
                this.metaData.measure = measure;
                this.metaData.mode = mode;
                this.metaData.stacked = stacked;
                this.metaData.fields = fields;
                this.metaData.area = area;
                this.metaData.smooth = smooth;
                this.metaData.resModel = resModel;
                this.initialGroupBy = groupBy;
                await this.load(this.searchParams);
            }
        });
    }
}

class StudioGraphController extends GraphController {
}

StudioGraphController.template = "dynamic_odoo.GraphView";
StudioGraphController.props = {
    ...GraphController.props,
    ...viewStudioProps,
}

export const studioGraphView = {
    ...graphView,
    Model: StudioGraphModel,
    Controller: StudioGraphController
};

studioViewRegistry.add("graph_studio", studioGraphView);


