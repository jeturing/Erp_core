/** @odoo-module **/
import {archParseBoolean} from "@web/views/utils";
import {visitXML} from "@web/core/utils/xml";

export class DashboardArchParser {
    parse(arch) {
        const archInfo = {
            canResize: false,
            canDrag: false,
            cards: []
        };

        visitXML(arch, (node) => {
            switch (node.tagName) {
                case "kanban": {
                    if (node.hasAttribute("can_drag")) {
                        archInfo.canDrag = archParseBoolean(node.getAttribute("can_drag"));
                    }
                    if (node.hasAttribute("can_resize")) {
                        archInfo.canResize = archParseBoolean(node.getAttribute("can_resize"));
                    }
                    break;
                }
                case "card" : {
                    const card = {
                        arch: node.innerHTML,
                        position: {}
                    };
                    this.constructor.cardAttrs.map((attr) => {
                        card[attr[0]] = node.getAttribute(attr[1])
                    });
                    ["x", "y", "w", "h"].map((attr) => {
                        card.position[attr] = parseInt(node.getAttribute(attr));
                    });
                    archInfo.cards.push(card);
                }
            }
        });
        return archInfo;
    }
}

DashboardArchParser.cardAttrs = [["key", "key"], ["viewType", "view_type"], ["model", "model"], ["title", "title"]]
