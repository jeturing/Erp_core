/** @odoo-module **/

import {registry} from "@web/core/registry";
import {CalendarController} from "@web/views/calendar/calendar_controller";
import {calendarView} from "@web/views/calendar/calendar_view";
import {viewStudioProps} from "@dynamic_odoo/studio/center/view_components";

const studioViewRegistry = registry.category("studio_views");
const {onWillUpdateProps} = owl;


class StudioCalendarController extends CalendarController {
    static props = ["*"];
    setup() {
        super.setup();
        onWillUpdateProps(async (nextProps) => {
            Object.assign(this.model.meta, nextProps.archInfo)
            await this.model.load();
        });
    }
}

StudioCalendarController.template = "dynamic_odoo.CalendarView";

export const studioCalendarView = {...calendarView, Controller: StudioCalendarController};
studioViewRegistry.add("calendar_studio", studioCalendarView);


