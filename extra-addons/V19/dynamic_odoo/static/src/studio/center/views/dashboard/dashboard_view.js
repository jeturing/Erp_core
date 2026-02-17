/** @odoo-module **/

import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {jsonNodeToString, stringToJson} from "@dynamic_odoo/core/utils/view";
import {DashboardController} from "@dynamic_odoo/base/views/dashboard/dashboard_controller";
import {DashboardView} from "@dynamic_odoo/base/views/dashboard/dashboard_view";
import {DashboardRenderer} from "@dynamic_odoo/base/views/dashboard/dashboard_renderer";
import {DashboardCard} from "@dynamic_odoo/base/views/dashboard/dashboard_card";
import {DashboardArchParser} from "@dynamic_odoo/base/views/dashboard/dashboard_arch_parser";
import {ComponentModifierDialog} from "@dynamic_odoo/studio/center/modifier"
import {MODIFIER_DASHBOARD_COMPONENTS} from "./components/components";
import {floorRandom} from "@dynamic_odoo/core/utils/format";
import {_t} from "@web/core/l10n/translation";

const {useEffect, useSubEnv} = owl;
const studioViewRegistry = registry.category("studio_views");

class StudioDashboardArchParser extends DashboardArchParser {
}

StudioDashboardArchParser.cardAttrs = [...DashboardArchParser.cardAttrs, ["nodeId", "node-id"]];

class DashboardComponentModifierDialog extends ComponentModifierDialog {
    setup() {
        super.setup();
        const reload = () => {
            this.state.key = `modifier_${floorRandom()}`;
        }
        useEffect(() => {
            this.env.bus.addEventListener("MODIFIER-DIALOG:RELOAD", reload)
            return () => {
                this.env.bus.removeEventListener("MODIFIER-DIALOG:RELOAD", reload)
            }
        })

    }
}

class StudioDashboardCard extends DashboardCard {
    setup() {
        super.setup();
        this.dialog = useService("dialog");
        // useSubEnv({
        //     debug: false,
        // });
    }

    setComponent(component) {
        this.componentModifier = component;
    }

    async onDelete(e) {
        e.stopPropagation();
        this.env.bus.trigger("DASHBOARD:DO-CARD", {fncName: "onRemoveNode", params: [this.props.viewInfo.nodeId]})
    }

    async onCopy(e) {
        e.stopPropagation();
        this.env.bus.trigger("DASHBOARD:DO-CARD", {fncName: "onDuplicateNode", params: [this.props.viewInfo.nodeId]})
    }

    onShowModifier() {
        const self = this, {viewInfo} = this.props;
        const newViewInfo = {...viewInfo};
        newViewInfo.archJson = stringToJson(jsonNodeToString(viewInfo.archJson));
        this.dialog.add(DashboardComponentModifierDialog, {
            viewInfo: newViewInfo,
            title: "Edit Dashboard Widget",
            setComponent: this.setComponent.bind(this),
            Modifier: MODIFIER_DASHBOARD_COMPONENTS[newViewInfo.viewType],
            reset: () => {
                newViewInfo.archJson = stringToJson(jsonNodeToString(viewInfo.archJson));
                newViewInfo.model = viewInfo.model;
                newViewInfo.domain = viewInfo.domain;
            },
            confirm: () => {
                self.componentModifier.prepareDataToSave();
                self.env.bus.trigger("DASHBOARD:UPDATE-CARD", {
                    cards: [{
                        key: newViewInfo.key,
                        model: newViewInfo.model,
                        arch: stringToJson(jsonNodeToString(newViewInfo.archJson))
                    }]
                });
            }
        });
    }
}

StudioDashboardCard.template = "dynamic_odoo.StudioDashboardCard";

class StudioDashboardRenderer extends DashboardRenderer {
    get archInfo() {
        const archInfo = super.archInfo;
        archInfo.canDrag = true;
        archInfo.canResize = true;
        return archInfo;
    }

    prepareWrapWidgetAttr(viewInfo) {
        const {nodeId} = viewInfo;
        return [["node-id", nodeId]];
    }
}

StudioDashboardRenderer.DashboardCard = StudioDashboardCard;

class StudioDashboardController extends DashboardController {
    onGridChange(grid) {
        grid.on("change", (e, items) => {
            if (items) {
                const cards = items.map((item) => {
                    const cardKey = $(item.content).attr("data-key");
                    return {x: item.x, y: item.y, w: item.w, h: item.h, key: cardKey};
                });
                this.env.bus.trigger("DASHBOARD:UPDATE-CARD", {cards: cards});
            }
        });
    }
}

StudioDashboardController.template = "dynamic_odoo.StudioDashboardView";

export const studioActivityView = {
    ...DashboardView,
    ArchParser: StudioDashboardArchParser,
    Renderer: StudioDashboardRenderer,
    Controller: StudioDashboardController
};
studioViewRegistry.add("dashboard_studio", studioActivityView);


