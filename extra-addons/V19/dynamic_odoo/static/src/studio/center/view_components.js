/** @odoo-module **/

import {View} from "@web/views/view";
import {jsonNodeToXml} from "@dynamic_odoo/core/utils/view";

const {Component, onMounted, onPatched, xml} = owl;

export const viewStudioProps = {
    parent: {optional: true, type: Object},
    mode: {optional: true, type: String}
}

export class ViewComponent extends Component {
    setup() {
        super.setup();
        onMounted(() => {
            $(this.__owl__.bdom.el).data("component", this);
        });
        onPatched(() => {
            $(this.__owl__.bdom.el).data("component", this);
        });
    }

    get context() {
        const {context} = this.props.viewInfo;
        return {
            Studio: true,
            ...(context || {})
        }
    }

    get componentProps() {
        const {viewInfo, parent, componentProps} = this.props, {
            fields,
            archJson,
            relatedModels,
            model,
            domain,
            resId,
            viewType
        } = viewInfo;
        const props = {
            ...(componentProps || {}),
            parent: parent,
            resModel: model,
            type: viewType + "_studio",
            context: this.context,
            arch: jsonNodeToXml(archJson),
            relatedModels: relatedModels,
            selectRecord: async () => {
            },
            fields: fields,
            resId: resId,
            mode: "readonly",
            loadActionMenus: false,
            display: {
                controlPanel: false,
            },
            domain: domain || []
        }
        return props;
    }

    get componentInfo() {
        return {
            Component: View,
            componentProps: this.componentProps
        };
    }


}

ViewComponent.template = xml`<div t-att-class="props.classes"><t t-set="comInfo" t-value="componentInfo" /><t t-component="comInfo.Component" t-props="comInfo.componentProps" /></div>`;