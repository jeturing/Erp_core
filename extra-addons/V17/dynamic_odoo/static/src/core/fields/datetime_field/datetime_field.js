/** @odoo-module **/

import {DateTimeField} from "@web/views/fields/datetime/datetime_field";
import {
    deserializeDate,
    deserializeDateTime,
    formatDateTime,
    serializeDate,
    serializeDateTime,
} from "@web/core/l10n/dates";

const {Component} = owl;


class DateTimeFieldExtend extends DateTimeField {
    static props = ["*"];

    triggerIsDirty(isDirty) {
    }
}

export class StudioDateTimeField extends Component {

    get dateRangeProps() {
        this.START = this.START || `start_${Math.random()}`;
        this.END = this.END || `end_${Math.random()}`;
        const {value, type} = this.props;
        return {
            name: this.START,
            startDateField: this.START,
            endDateField: this.END,
            alwaysRange: true,
            record: {
                fields: {[this.START]: {type: type}, [this.END]: {type: type}},
                data: {
                    [this.START]: this.serverToClient(value?.start || false),
                    [this.END]: this.serverToClient(value?.end || false)
                },
                update: (val) => {
                    const start = val[this.START], end = val[this.END];
                    if (start && end) {
                        this.props.update({start: this.clientToServer(start), end: this.clientToServer(end)});
                    }
                }
            }
        }
    }

    get datetimeProps() {
        this.NAME = this.NAME || `datetime_${Math.random()}`;
        const {value, type} = this.props;
        return {
            name: this.NAME,
            record: {
                fields: {[this.NAME]: {type: type}},
                data: {[this.NAME]: this.serverToClient(value)},
                update: (val) => {
                    this.props.update(this.clientToServer(val[this.NAME]));
                },
            },
        }
    }

    clientToServer(value) {
        const {type} = this.props;
        if (!value) return value;
        return type == "date" ? serializeDate(value) : serializeDateTime(value);
    }

    serverToClient(value) {
        const {type} = this.props;
        if (!value) return value;
        return type == "date" ? deserializeDate(value) : deserializeDateTime(value);
    }
}

StudioDateTimeField.defaultProps = {type: "datetime"}
StudioDateTimeField.template = "dynamic_odoo.DateTimeField";
StudioDateTimeField.components = {DateTimeField: DateTimeFieldExtend}