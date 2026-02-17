/** @odoo-module **/

import {registry} from "@web/core/registry";
import {ActivityController} from "@mail/views/web/activity/activity_controller";
import {activityView} from "@mail/views/web/activity/activity_view";

const studioViewRegistry = registry.category("studio_views");


class StudioActivityController extends ActivityController {
}

StudioActivityController.template = "dynamic_odoo.ActivityView";

export const studioActivityView = {...activityView, Controller: StudioActivityController};
studioViewRegistry.add("activity_studio", studioActivityView);


