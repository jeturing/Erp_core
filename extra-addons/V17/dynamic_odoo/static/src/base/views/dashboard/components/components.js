/** @odoo-module **/

import {Title} from "./title/title";
import {Battery} from "./battery/battery";
import {CountDown} from "./countdown/countdown";
import {Youtube} from "./youtube/youtube";
import {Text} from "./text/text";
import {Bookmarks} from "./bookmarks/bookmarks";
import {ViewComponent} from "@dynamic_odoo/studio/center/view_components";

const {Component, xml} = owl;


export const DashboardWidgets = {
    battery: {
        label: "Battery",
        desc: "Your progress in a glance",
        thumb: "buttery_png.png",
        icon: "battery_icon.png",
        component: Battery,
    },
    title: {
        label: "Title",
        desc: "Your title in a glance",
        thumb: "number_png.png",
        icon: "number_icon.png",
        component: Title,
    },
    graph: {
        label: "Graph",
        desc: "Create graph views to visually show data in your board",
        thumb: "chart_png.png",
        icon: "chart_icon.png",
        component: ViewComponent,
    },
    pivot: {
        label: "Pivot",
        name: "pivot",
        desc: "Create Pivot views to visually show data in your board",
        thumb: "quote_png.png",
        component: ViewComponent,
    },
    calendar: {
        label: "Calendar",
        name: "calendar",
        desc: "Create Calendar views to visually show data in your board",
        thumb: "calendar.png",
        component: ViewComponent,
    },
    list: {
        label: "Table",
        name: "list",
        desc: "View your projects data in a glance",
        thumb: "list_png.png",
        component: ViewComponent,
    },
    rich_text: {
        label: "Text",
        name: "pivot",
        desc: "Add rich text to your dashboard.",
        thumb: "text_png.png",
        component: Text
    },
    countdown: {
        label: "Countdown",
        name: "pivot",
        desc: "Stay on track with countdown",
        thumb: "countdown_png.png",
        component: CountDown,
    },
    youtube: {
        label: "Youtube",
        name: "pivot",
        desc: "Add a video from YouTube to view it whenever you want",
        thumb: "youtube_png.png",
        component: Youtube,
    },
    bookmarks: {
        label: "Bookmarks",
        name: "pivot",
        desc: "Collect articles, ideas & stories from anywhere.",
        thumb: "bookmarks_png.png",
        component: Bookmarks,
    },
};


export class DashboardComponent extends Component {
    setup() {
        super.setup();
        this.DashboardWidget = DashboardComponent.ComponentStore[this.props.viewInfo.viewType].component;
    }

    get componentProps() {
        return {};
    }
}

DashboardComponent.template = xml`<t t-component="DashboardWidget" t-props="{viewInfo: props.viewInfo, componentProps: componentProps}" />`;
DashboardComponent.ComponentStore = {...DashboardWidgets};