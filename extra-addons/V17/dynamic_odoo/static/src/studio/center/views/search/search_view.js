/** @odoo-module **/

import {SearchArchParser} from "@web/search/search_arch_parser";
import {jsonNodeToXml} from "@dynamic_odoo/core/utils/view";

const {Component} = owl;

class StudioSearchArchParser extends SearchArchParser {
    constructor(searchViewDescription, fields, searchDefaults = {}, searchPanelDefaults = {}) {
        super(searchViewDescription, fields, searchDefaults, searchPanelDefaults);
    }

    setNodeId(node) {
        this.currentGroup[this.currentGroup.length - 1].nodeId = node.getAttribute("node-id");
    }

    visitField(node) {
        super.visitField(node);
        this.setNodeId(node);
    }

    visitFilter(node) {
        super.visitFilter(node);
        this.setNodeId(node);
        this.setSeparator(node);
    }

    setSeparator(node) {
        const nodeId = node.getAttribute("node-id");
        const findNode = this.viewInfo.archJson.params.findNode(false,
            (item) => item.attrs && item.attrs['node-id'] == nodeId);
        const children = findNode.parentNode.children;
        const findIndex = children.findIndex(
            (_node) => _node.attrs && _node.attrs['node-id'] == findNode.nodeId);
        const nextNode = children[findIndex + 1];
        if (nextNode && nextNode.tag == "separator") {
            this.currentGroup.push({type: "separator", nodeId: nextNode.nodeId});
        }
    }
}

export class SearchView extends Component {
    get searchData() {
        return [
            {
                type: "field",
                string: "Automation Fields",
                icon: "fa fa-magic",
                data: this.getSearchData(["field"], false)
            },
            {
                type: "filter",
                string: "Filters",
                icon: "fa fa-filter",
                data: this.getSearchData(["filter", "dateFilter"])
            },
            {
                type: "groupBy",
                string: "Groups",
                icon: "fa fa-bars",
                data: this.getSearchData(["groupBy", "dateGroupBy"])
            },
        ]
    }

    getSearchData(types = [], useSeperator = true) {
        const {viewInfo} = this.props;
        const searchViewDescription = {arch: jsonNodeToXml(viewInfo.archJson), irFilters: [], viewId: false};
        const searchViewFields = viewInfo.fields;
        const parser = new StudioSearchArchParser(searchViewDescription, searchViewFields);
        parser.viewInfo = viewInfo;
        parser.parse();

        const result = []
        parser.preSearchItems.map((items) => {
            items.map((item, index) => {
                if (types.includes(item.type)) {
                    result.push(item);
                    const nextItem = items[index + 1];
                    if (useSeperator && nextItem && nextItem.type == "separator") {
                        result.push(nextItem)
                    }
                }
            });
        });
        return result;
    }
}

SearchView.template = "dynamic_odoo.SearchView";


