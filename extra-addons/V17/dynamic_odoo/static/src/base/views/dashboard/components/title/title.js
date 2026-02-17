/** @odoo-module **/

import {formatNumber, roundNumber} from "@dynamic_odoo/core/utils/format";
import {jsonNodeToXml} from "@dynamic_odoo/core/utils/view";

const {Component, onWillUpdateProps, onWillStart, xml} = owl;

export class Title extends Component {
    get fields() {
        const {fields} = this.props.viewInfo;
        return Object.values(fields).filter((field) => field.store && ["integer", "float", "monetary"].includes(field.type) && field.name != "id").map((field) => field.name)
    }

    setup() {
        super.setup();
        this.setTemplate();
        onWillStart(async () => {
            await this.loadData();
        });
        onWillUpdateProps(async (nextProps) => {
            await this.loadData(nextProps);
            this.setTemplate();
        });
    }

    setTemplate() {
        const {viewInfo} = this.props, {archJson} = viewInfo;
        this.template = xml`${jsonNodeToXml(archJson.children[0])}`;
    }

    getLabel(type, measure) {
        if (type && measure && this.groups.length) {
            const data = {}, getTotal = (sumName) => this.groups.reduce((total, group) => total + group[sumName], 0);
            data.sum = getTotal(measure);
            data.count = getTotal("__count");
            data.average = data.sum / data.count;
            return formatNumber(roundNumber(data[type] || 0));
        }
        return 0;
    }

    async loadData(props = this.props) {
        const {domain, model} = props.viewInfo;
        this.groups = await this.env.services.orm.readGroup(model, domain, this.fields, []);
        this.modelName = model;
    }
}

Title.template = xml`<div class="dbWidgetTitle"><t t-call="{{template}}" /></div>`;
