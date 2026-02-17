/** @odoo-module **/
import {NodeModifier} from "@dynamic_odoo/studio/center/modifier";
import {jsonNodeToString} from "@dynamic_odoo/core/utils/view";

const {toRaw} = owl;
const supperRootModel = NodeModifier.nodeProps.root_model;
export const ROOT_MODEL = (attrs = ["domain", "group_by", "measure", "col", "row", "model_access_rights"], do_something = () => {
}) => {
    return {
        ...supperRootModel, modifierProps: {
            ...supperRootModel.modifierProps, onChange: async (node, prop, value, params) => {
                toRaw(node).attrs.model = value;
                attrs.map((attr) => {
                    delete toRaw(node).attrs[attr];
                });
                const {viewInfo, app} = params.self.params;
                const newViewInfo = await app.env.services.orm.call("ir.ui.view", "prepare_view_info", [jsonNodeToString(viewInfo.archJson), value, viewInfo.viewType], {});
                viewInfo.domain = [];
                viewInfo.model = value;
                viewInfo.fields = newViewInfo.fields;
                viewInfo.relatedModels = newViewInfo.relatedModels;
                do_something(node, prop, value, params);
            }
        }
    }
}