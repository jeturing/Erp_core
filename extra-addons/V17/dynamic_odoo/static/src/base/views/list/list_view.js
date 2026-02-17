/** @odoo-module **/

import {ListArchParser} from "@web/views/list/list_arch_parser";
import {ListRenderer} from "@web/views/list/list_renderer";
import {archParseBoolean} from "@web/views/utils";
import {SearchInTree} from "./search_in_tree/search_in_tree";
import {patch} from "@web/core/utils/patch";


patch(ListArchParser.prototype, {
    parse(xmlDoc, models, modelName) {
        this.searchInTree = archParseBoolean(xmlDoc.getAttribute("search_in_tree"));
        const parseInfo = super.parse(xmlDoc, models, modelName);
        parseInfo.searchInTree = this.searchInTree;
        return parseInfo;
    }
});


ListRenderer.components = {...ListRenderer.components, SearchInTree}
