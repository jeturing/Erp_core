/** @odoo-module **/

import {jsonNodeToXml} from "@dynamic_odoo/core/utils/view";
import {deserializeDateTime,} from "@web/core/l10n/dates";

const {DateTime} = luxon;
const {Component, onMounted, onWillUnmount, useState, onWillUpdateProps, xml} = owl;

export class CountDown extends Component {

    setup() {
        super.setup();
        this.setTemplate();
        this.state = useState({days: 0, hours: 0, minutes: 0, seconds: 0});
        this.setState();
        onWillUpdateProps(async (nextProps) => {
            this.setTemplate();
        });
        onMounted(() => {
            const self = this;
            this.interval = setInterval(() => {
                self.setState();
            }, 1 * 1000);
        });
        onWillUnmount(() => clearInterval(this.interval));
    }

    setState() {
        if (this.date_stop) {
            const now = DateTime.now(),
                remaining = this.date_stop.diff(now, ["days", "hours", "minutes", "seconds"]);
            if (remaining < 0) {
                return clearInterval(this.interval);
            }
            Object.assign(this.state, {...remaining.toObject()});
        }
    }

    setTemplate() {
        const {viewInfo} = this.props, {archJson, model} = viewInfo;
        const resModel = archJson.attrs.model || model;
        archJson.attrs.model = resModel;
        if (archJson.attrs.date_stop) {
            this.date_stop = deserializeDateTime(archJson.attrs.date_stop);
        }
        this.template = xml`${jsonNodeToXml(archJson.children[0])}`;
    }
}

CountDown.template = xml`<t t-call="{{template}}" />`;
