/** @odoo-module **/

import {ComponentModifier} from "../modifier";
import {xmlToJson, jsonNodeToString} from "@dynamic_odoo/core/utils/view";

export class ViewComponentModifier extends ComponentModifier {
    prepareDataToSave() {
        const {viewInfo, key} = this.props, {viewType, model} = viewInfo;
        const data = super.prepareDataToSave();
        data.res_model = model;
        data.view_key = key;
        data.view_type = viewType;
        return data;
    }
}