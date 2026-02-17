/** @odoo-module **/

import {registry} from "@web/core/registry";
import {NodeModifier} from "@dynamic_odoo/studio/center/modifier";
import {DashboardWidgets} from "@dynamic_odoo/base/views/dashboard/components/components";
import {DashboardComponent, MODIFIER_DASHBOARD_COMPONENTS} from "./components/components";
import {ViewComponentModifier} from "../view_modifier";
import {DRAG_COMPONENTS} from "./drag_component";
import {getTemplate, stringToJson} from "@dynamic_odoo/core/utils/view";
import {floorRandom} from "@dynamic_odoo/core/utils/format";
import {evaluateBooleanExpr} from "@web/core/py_js/py";

const {Component, toRaw, onPatched, useEffect} = owl;

const modifierRegistry = registry.category("modifier_views");

class ListComponents extends Component {
    setup() {
        this.DashboardWidgets = DashboardWidgets;
        this.MD_COMPONENTS = MODIFIER_DASHBOARD_COMPONENTS;
    }
}

ListComponents.components = {DashboardComponent, DragDashboardComponent: DRAG_COMPONENTS.DragDashboardComponent}

ListComponents.template = "dynamic_odoo.Dashboard.TabComponents";

const PROPS = {
    list_component: {
        type: String, optional: true, noLabel: true, modifierProps: {
            component: ListComponents, onChange: () => {
            },
            widgetProps: () => {

            }
        }
    },
    title: {type: String, optional: true}
}

class DashboardNodeModifier extends NodeModifier {
}

DashboardNodeModifier.nodeProps = {
    ...NodeModifier.nodeProps, ...PROPS
}
DashboardNodeModifier.nodeViewStore = [
    ...NodeModifier.nodeViewStore,
    ["[card]", (node) => {
        const view = ["title", "more"];
        if (evaluateBooleanExpr(node.attrs.no_title)) {
            view.splice(0, 1);
        }
        return view;
    }],
    ["[dashboard]", ["list_component"]],
]


export class DashboardModifier extends ViewComponentModifier {
    setup() {
        super.setup();
        const newCard = (payload) => {
            const {widgetName, archTemplate} = payload.detail;
            this.newCard.bind(this)(widgetName, archTemplate)
        };
        const updateCard = (payload) => {
            const {archJson} = this.props.viewInfo, {cards} = payload.detail;
            cards.map((card) => {
                if (card.arch) {
                    const index = archJson.children.findIndex((node) => node.tag == "card" && node.attrs.key == card.key);
                    archJson.children[index].children = [card.arch];
                }
                const cardNode = this.findNode(false, (node) => node.tag == "card" && node.attrs.key == card.key);
                Object.keys(card).map((attr) => {
                    if (!["arch", "key"].includes(attr)) {
                        toRaw(cardNode).attrs[attr] = card[attr];
                    }
                });
            });
        }
        const doSomething = (payload) => {
            const {fncName, params} = payload.detail;
            this[fncName](...params);
        }
        useEffect(() => {
            this.env.bus.addEventListener("DASHBOARD:DO-CARD", doSomething);
            this.env.bus.addEventListener("DASHBOARD:UPDATE-CARD", updateCard);
            this.env.bus.addEventListener("DASHBOARD:NEW-CARD", newCard);
            return () => {
                this.env.bus.removeEventListener("DASHBOARD:DO-CARD", doSomething);
                this.env.bus.removeEventListener("DASHBOARD:UPDATE-CARD", updateCard);
                this.env.bus.removeEventListener("DASHBOARD:NEW-CARD", newCard);
            };
        });
    }

    async newCard(cardName, template) {
        const {viewInfo} = this.props, {model, archJson} = viewInfo;
        const arch = template ? getTemplate(template) : document.createElement(cardName).outerHTML,
            position = {x: 0, y: 0, w: 8, h: 4};
        if (["graph"].includes(cardName)) {
            position.w = 12;
            position.h = 8;
        }
        const cardArchJson = stringToJson(arch);
        cardArchJson.attrs.model = model;
        const newCard = {
            attrs: {...position, view_type: cardName, key: `card_${floorRandom()}`, model: model},
            tag: "card",
            children: [cardArchJson],
            parentId: archJson.nodeId,
        }
        newCard.attrs.no_title = ["title", "countdown", "rich_text", "youtube"].includes(cardName);
        this.setNodeId(newCard);
        archJson.children.push(newCard);
    }

    onDuplicateNode(node) {
        super.onDuplicateNode(node);
        this.state.node.attrs.key = `card_${floorRandom()}`;
    }

    onClickNode(e) {
        const el = $(e.currentTarget), node = this.nodes[el.closest("[node-id]").attr("node-id")];
        if (node.tag == "card") {
            super.onClickNode(e);
        }
    }
}

DashboardModifier.useStructure = true;
DashboardModifier.showNodeRoot = true;
DashboardModifier.classes = "studio_dashboard_view";
DashboardModifier.NodeModifier = DashboardNodeModifier;
DashboardModifier.components = {...ViewComponentModifier.components};
DashboardModifier.ArchTemplate = "dynamic_odoo.Dashboard.View.default";


modifierRegistry.add("dashboard", DashboardModifier);

