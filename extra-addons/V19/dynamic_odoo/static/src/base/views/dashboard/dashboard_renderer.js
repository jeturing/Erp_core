/** @odoo-module **/

import {templates} from "@web/core/assets";
import {DashboardCard} from "./dashboard_card";
import {stringToJson} from "@dynamic_odoo/core/utils/view";
import {floorRandom} from "@dynamic_odoo/core/utils/format";
import {Domain} from "@web/core/domain";

const {Component, onPatched, onWillStart, mount, onMounted, onWillUpdateProps, useEffect, onWillDestroy} = owl;

export class DashboardRenderer extends Component {
    get archInfo() {
        return this.props.archInfo;
    }

    setup() {
        super.setup();
        this.model = this.props.model;
        this.cardStore = {};
        const reloadGrid = () => this.reloadGrid.bind(this)();
        onWillStart(async () => {
            await this.loadComponentViewInfo(this.archInfo.cards);
        });
        onWillUpdateProps(async (nextProps) => {
            await this.loadComponentViewInfo(nextProps.archInfo.cards);
        });
        onMounted(async () => {
            await this.renderGridStack();
            this.__owl__.parent.parent.renderer = this;
        });
        onPatched(async () => {
            await this.renderGridStack();
            this.__owl__.parent.parent.renderer = this;
        });
        useEffect(() => {
            // await this.renderGridStack();
            // this.__owl__.parent.parent.renderer = this;
            this.env.bus.addEventListener("DASHBOARD:RELOAD", reloadGrid);
            return () => this.env.bus.removeEventListener("DASHBOARD:RELOAD", reloadGrid);
        });
        onWillDestroy(() => {
            Object.values(this.cardStore).map((card) => {
                card.__owl__.destroy();
            });
        });

    }

    async loadComponentViewInfo(cards) {
        this.viewsInfo = await this.env.services.orm.call("ir.ui.view", "prepare_views_info", [cards], {});
        this.viewsInfo.map((viewInfo) => {
            viewInfo.archJson = stringToJson(viewInfo.arch);
            const {domain, model} = viewInfo.archJson.attrs;
            viewInfo.domain = (new Domain(domain || '[]')).toList({});
            viewInfo.model = model || viewInfo.model;
        });
    }

    async reloadGrid() {
        await this.model.load();
        await this.renderGridStack();
    }

    async reloadStackItem(cardData) {
        await this.model.load();
        const dataUpdate = this.model.data.filter((d) => d.id == cardData.id);
        if (dataUpdate.length) {
            cardData.card.props.viewInfo = dataUpdate[0].viewInfo;
            cardData.card.__owl__.render();
        }
    }

    ohDestroy() {
        if (this.grid) {
            Object.values(this.cardStore).map((card) => {
                card.__owl__.destroy();
            });
            this.grid.destroy();
        }
    }

    prepareWrapWidgetAttr(viewInfo) {
        return [["data-key", viewInfo.key]];
    }

    async renderGridStack() {
        this.ohDestroy();
        const {canResize, canDrag} = this.archInfo, gridKey = `grid_${floorRandom()}`, $el = $(this.__owl__.bdom.el);
        $el.find(".grid-stack").remove();
        $el.append($(`<div class="grid-stack ${gridKey}" />`));
        this.grid = GridStack.init({
            alwaysShowResizeHandle: /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
                navigator.userAgent
            ),
            resizable: {
                handles: 'e, se, s, sw, w'
            },
            column: 36,
            acceptWidgets: true,
            dragIn: '.newWidget',  // class that can be dragged from outside
            dragInOptions: {revert: 'invalid', scroll: false, appendTo: 'body', helper: 'clone'},
            removable: '#trash', // drag-out delete class
            removeTimeout: 100,
            disableResize: !canResize,
            disableDrag: !canDrag,
        }, `.grid-stack.${gridKey}`);
        const items = [];
        this.viewsInfo.map(async (viewInfo) => {
            const {position, key} = viewInfo;
            const attrs = this.prepareWrapWidgetAttr(viewInfo).map((attr) => `${attr[0]}='${attr[1]}'`).join(" ");
            items.push({
                ...position,
                content: "<div class='wWidget' data-key='" + key + "' " + attrs + " ></div>"
            });
        });

        this.grid.load(items);
        this.viewsInfo.map(async (viewInfo) => {
            await this.renderCard(viewInfo);
        });
        this.props.onGridChange(this.grid);
    }

    async renderCard(viewInfo) {
        const $el = $(this.__owl__.bdom.el),
            $wrap = $el.find(`.wWidget[data-key='${viewInfo.key}']`),
            $item = $wrap.parents(".grid-stack-item");
        const card = await mount(this.constructor.DashboardCard, $wrap[0], {
            templates,
            env: this.env,
            props: {
                viewInfo: viewInfo,
                onShowCenter: this.props.onShowCenter,
                elStackItem: $item,
                parent: this,
                showTitle: !["title", "countdown", "rich_text", "youtube"].includes(viewInfo.viewType),
                canExport: ["graph"].includes(viewInfo.viewType)
            },
            position: "first-child"
        });
        if ($item.length) {
            $item.attr({'widget_type': viewInfo.viewType});
        }
        this.cardStore[viewInfo.key] = card;
    }
}

DashboardRenderer.template = "dynamic_odoo.DashboardRenderer";
DashboardRenderer.props = ["model", "onCardClick", "onGridChange", "archInfo", "onShowCenter"];
DashboardRenderer.defaultProps = {};
DashboardRenderer.components = {};
DashboardRenderer.DashboardCard = DashboardCard;
