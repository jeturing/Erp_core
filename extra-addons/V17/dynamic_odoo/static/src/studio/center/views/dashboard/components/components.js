/** @odoo-module **/

import {DashboardWidgets} from "@dynamic_odoo/base/views/dashboard/components/components";
import {TitleModifier} from "./title/title";
import {BatteryModifier} from "./battery/battery";
import {DashboardCalendarModifier} from "./calendar/calendar";
import {DashboardListModifier} from "./list/list";
import {DashboardPivotModifier} from "./pivot/pivot";
import {DashboardGraphModifier} from "./graph/graph";
import {CountdownModifier} from "./countdown/countdown";
import {YoutubeModifier} from "./youtube/youtube";
import {TextModifier} from "./text/text";
import {BookmarksModifier} from "./bookmarks/bookmarks";

const {Component} = owl;

export const MODIFIER_DASHBOARD_COMPONENTS = {
    battery: BatteryModifier,
    title: TitleModifier,
    graph: DashboardGraphModifier,
    pivot: DashboardPivotModifier,
    calendar: DashboardCalendarModifier,
    list: DashboardListModifier,
    countdown: CountdownModifier,
    youtube: YoutubeModifier,
    rich_text: TextModifier,
    bookmarks: BookmarksModifier,
}

export class DashboardComponent extends Component {

    get componentInfo() {
        return DashboardWidgets[this.props.type];
    }

    get componentModifier() {
        return MODIFIER_DASHBOARD_COMPONENTS[this.props.type];
    }
}

DashboardComponent.template = "dynamic_odoo.Dashboard.Component";