/** @odoo-module **/

import {Domain} from "@web/core/domain";
import {Field} from "@dynamic_odoo/core/fields/field";
import {useBus} from "@web/core/utils/hooks";


const {Component, useState} = owl;

export class SearchInTree extends Component {
    setup() {
        super.setup();
        this.state = useState({});
        useBus(this.env.searchModel, "update", () => {
            this.compareQueryValue();
        });
    }


    get searchItemsAdvance() {
        const {searchModel} = this.env, {searchItems} = searchModel;
        return Object.keys(searchItems).filter((itemKey) => searchItems[itemKey].search_advance == this.props.field.name);
    }

    get fieldsSupported() {
        return {
            integer: {},
            float: {},
            monetary: {},
            char: {},
            datetime: {props: {type: "datetime", useRange: true}},
            many2one: {find: ["relation"], props: {value_name: "id"}},
            many2many: {find: ["relation"], props: {value_name: "id"}, operator: "in"},
            selection: {find: [["selection", "options"]]}
        }
    }

    get fieldProps() {
        const {field} = this.props, {type} = field, fieldSupported = this.fieldsSupported[type];
        if (fieldSupported) {
            const props = fieldSupported.props || {};
            (fieldSupported.find || []).map((prop) => {
                const isArray = typeof prop !== "string";
                props[isArray ? prop[1] : prop] = field[isArray ? prop[0] : prop];
            });
            if (this.state.value) {
                props.value = this.state.value;
            }
            return {
                type: type, props: {
                    ...props,
                    update: (value) => this.onSearch(value)
                }
            }
        }
    }

    prepareDataToSearch() {
        const {value} = this.state, {name, string, type} = this.props.field, {operator} = this.fieldsSupported[type];
        const prepareDomain = () => {
            const domain = [];
            if (["date", "datetime"].includes(type)) {
                domain.push([name, '>=', value.start]);
                domain.push([name, '<=', value.end]);
            } else {
                domain.push([name, operator || "ilike", value || '']);
            }
            return domain;
        }
        return {
            type: 'filter',
            description: `Filter by ${string}`,
            search_advance: name,
            domain: (new Domain(prepareDomain())).toString()
        };
    }

    compareQueryValue() {
        const {query} = this.env.searchModel;
        this.searchItemsAdvance.map((itemKey) => {
            const index = query.findIndex((queryElem) => queryElem.searchItemId === parseInt(itemKey));
            if (index < 0) {
                this.state.value = false;
            }
        });
    }

    removeFilterByName() {
        const {searchItems, query} = this.env.searchModel;
        this.searchItemsAdvance.map((itemKey) => {
            const index = query.findIndex((queryElem) => queryElem.searchItemId === parseInt(itemKey));
            if (index >= 0) {
                query.splice(index, 1);
            }
            delete searchItems[itemKey];
        })
    }

    onSearch(value) {
        this.state.value = value;
        this.removeFilterByName();
        this.env.searchModel.createNewFilters([this.prepareDataToSearch()]);
    }

    onStop(e) {
        e.stopPropagation();
    }
}

SearchInTree.template = "dynamic_odoo.searchInTree";
SearchInTree.components = {Field};