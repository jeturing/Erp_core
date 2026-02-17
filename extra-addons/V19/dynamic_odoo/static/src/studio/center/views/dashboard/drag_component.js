/** @odoo-module **/
import {
    DragComponent,
} from "@dynamic_odoo/core/widgets/drag_component/drag_component";

class DragDashboardComponent extends DragComponent {

}

DragDashboardComponent.sortParams = {
    ...DragComponent.sortParams,
    selector: ".studio_dashboard_view",
    withoutSelector: ".o_dashboard_view",
    isNew: true,
    params: {
        tolerance: 'intersect',
    },
    lifecycle: {
        stop(event, ui, superFnc, params) {
            const component = params.getComponent(ui.item);
            const {widgetName, archTemplate} = component.props;
            params.env.bus.trigger("DASHBOARD:NEW-CARD", {widgetName, archTemplate});
            ui.item.remove();
        }
    },
}
export const DRAG_COMPONENTS = {
    DragDashboardComponent,
}