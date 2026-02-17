/** @odoo-module **/

import {Many2ManyTagsField} from "@web/views/fields/many2many_tags/many2many_tags_field";

const {Component, onWillPatch, onWillStart, onWillUpdateProps, useState} = owl;

class StudioMany2ManyTagsField extends Many2ManyTagsField {
    setup() {
        super.setup();
        this.update = this.props.update;
    }

    getDomain() {
        return this.props.domain;
    }

    get relation() {
        return this.props.relation;
    }

    get tags() {
        return [];
    }
}

StudioMany2ManyTagsField.props = {
    ...Many2ManyTagsField.props,
    relation: {type: String, optional: true},
    update: {type: Function, optional: true},
}

export class Many2manyField extends Component {
    setup() {
        super.setup();
        const {value} = this.props;
        this.state = useState({value: value || []});
        onWillStart(async () => {
            await this.prepareValueInfo();
        });
        onWillUpdateProps(async (nextProps) => {
            await this.prepareValueInfo(nextProps);
        });
    }

    async prepareValueInfo(props = this.props) {
        const {relation, domain, value_name, value} = props;
        this.valueInfo = {};
        if (Array.isArray(value)) {
            const valueInfo = await this.env.services.orm.searchRead(relation, [...(domain || []), [value_name, 'in', value]], ["id", "display_name", value_name]);
            valueInfo.map((info) => {
                this.valueInfo[info[value_name]] = info;
            });
        }
        this.state.value = value;
        return [];
    }

    async onChange(val) {
        const {relation, update, value_name} = this.props;
        if (value_name != "id") {
            val = await this.env.services.orm.searchRead(relation, [["id", "=", val[0].id]], [value_name, "model"]);
        }
        this.state.value.push(val[0][value_name]);
        update(this.state.value);
    }

    get m2mProps() {
        const self = this, {relation, domain, value_name} = this.props;
        return {
            name: "many2many_field",
            string: "Many2many Tags",
            record: {},
            domain: [[value_name, "not in", Object.values(this.valueInfo).map((val) => val[value_name])]].concat(domain || []),
            relation: relation,
            update: async (val) => {
                await self.onChange(val)
            },
        };
    }

    onCloseTag(tagName) {
        this.state.value.splice(this.state.value.indexOf(tagName), 1);
        this.props.update(this.state.value);
    }
}

Many2manyField.template = "dynamic_odoo.Many2manyField";
Many2manyField.defaultProps = {
    value: [],
};
Many2manyField.components = {
    StudioMany2ManyTagsField,
};
Many2manyField.props = {
    value_name: {type: String, optional: true},
    update: {type: Function, optional: true},
    value: {type: Array, optional: true},
    relation: {type: String, optional: true},
    domain: {type: Array, optional: true},
}

export class Many2manyGroups extends Many2manyField {
    async prepareValueInfo() {
        const {value} = this.state;
        this.valueInfo = {};
        this.state.value = value || [];
        if (Array.isArray(value) && value.length) {
            this.valueInfo = await this.xmlToResIds(value);
        }
    }

    async xmlToResIds(xmlIds) {
        return await this.env.services.orm.call("ir.model.data", "xmlid_to_res_ids", [xmlIds])
    }

    async resIdsToXml(res_ids = []) {
        const result = await this.env.services.orm.searchRead("ir.model.data", [['model', '=', 'res.groups'], ["res_id", "in", res_ids]], ["complete_name"]);
        return result.map((record) => record['complete_name']).join(",");
    }

    async onChange(val) {
        const xmlIds = await this.resIdsToXml([val[0].id])
        this.state.value.push(xmlIds);
        this.props.update(this.state.value);
    }
}