/** @odoo-module **/

import {registry} from "@web/core/registry";
import {PivotController} from "@web/views/pivot/pivot_controller";
import {PivotModel} from "@web/views/pivot/pivot_model";
import {PivotRenderer} from "@web/views/pivot/pivot_renderer";
import {pivotView} from "@web/views/pivot/pivot_view";
import {viewStudioProps} from "@dynamic_odoo/studio/center/view_components";

const studioViewRegistry = registry.category("studio_views");
const {onWillUpdateProps} = owl;


class StudioPivotModel extends PivotModel {
    setup(params) {
        super.setup(params);
        onWillUpdateProps(async (nextProps) => {
            const {context, modelParams} = nextProps;
            if (context.Studio) {
                const {activeMeasures, fields, resModel, colGroupBys, rowGroupBys} = modelParams.metaData;
                this.metaData.activeMeasures = activeMeasures;
                this.metaData.colGroupBys = colGroupBys;
                this.metaData.rowGroupBys = rowGroupBys;
                this.metaData.fields = fields;
                this.metaData.resModel = resModel;
                this.data.counts = {};
                await this.load(this.searchParams);
            }
        });
    }
}

class StudioPivotController extends PivotController {
}

StudioPivotController.template = "dynamic_odoo.PivotView";
StudioPivotController.props = {
    ...PivotController.props,
    ...viewStudioProps,
}

class StudioPivotRenderer extends PivotRenderer {
    static props = ["*"];
}

export const studioPivotView = {
    ...pivotView,
    Renderer: StudioPivotRenderer,
    Model: StudioPivotModel,
    Controller: StudioPivotController
};
studioViewRegistry.add("pivot_studio", studioPivotView);


