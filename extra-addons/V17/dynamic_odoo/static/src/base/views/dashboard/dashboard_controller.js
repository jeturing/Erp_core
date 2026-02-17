/** @odoo-module **/

import {useService} from "@web/core/utils/hooks";
import {Layout} from "@web/search/layout";
import {useModel} from "@web/model/model";
import {standardViewProps} from "@web/views/standard_view_props";
import {getTemplate} from "@dynamic_odoo/core/utils/view";

const {Component, useState} = owl;


export class DashboardController extends Component {
    setup() {
        super.setup();
        this.state = useState({
            showCenter: false,
        });

        this.actionService = useService("action");
        this.model = useModel(this.props.Model, {
            ...this.props.archInfo,
            context: this.props.context,
            resModel: this.props.resModel,
            domain: this.props.domain,
            fields: this.props.fields,
        });
    }

    onCardClick() {
    }

    get centerParams() {
        return this.center_params || {type: "choose", viewInfo: {}};
    }

    onShowCenter(widgetName, centerType = "choose", cardData = {}) {
        this.center_params = {type: centerType, cardData: cardData};
        this.state.showCenter = true;
    }

    async onCloseCenter(reload = true) {
        this.state.showCenter = false;
        if (reload) {
            await this.__owl__.renderer.reloadStackItem(this.center_params.cardData);
        }
    }

    onGridChange(grid) {
        // if (grid) {
        //     grid.on("change", (e, items) => {
        //         if (items) {
        //             const data = items.map((item) => {
        //                 const cardId = parseInt($(item.content).attr("data-id"));
        //                 return {x: item.x, y: item.y, w: item.w, h: item.h, id: cardId};
        //             });
        //             this.model['updateCard'](data);
        //         }
        //     });
        // }
    }

    async createNewCard(cardName, template) {
        const {viewId} = this.env.config, widgetId = _.uniqueId('DBoard'), {resModel} = this.props;
        const arch = template ? getTemplate(template) : document.createElement(cardName).outerHTML,
            position = {x: 0, y: 0, w: 8, h: 4};
        if (["graph"].includes(cardName)) {
            position.w = 12;
            position.h = 8;
        }
        const cardData = {
            arch: arch,
            title: "New Widget",
            name: `view_center.dashboard.${cardName}.${widgetId}`,
            model: resModel,
            view_id: viewId,
            view_type: cardName,
            ...position
        };
        await this.model.createNewCard(cardData);
        await this.onCloseCenter(false);
        await this.__owl__.renderer.reloadGrid();
    }
}

DashboardController.template = "dynamic_odoo.DashboardView";
DashboardController.components = {Layout};

DashboardController.props = {
    ...standardViewProps,
    Model: Function,
    // buttonTemplate: String,
    // modelParams: Object,
    archInfo: Object,
    Renderer: Function,
};
