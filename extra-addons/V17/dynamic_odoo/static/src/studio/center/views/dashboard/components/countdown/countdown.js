/** @odoo-module **/

import {NodeModifier, ComponentModifier, ComponentTabsModifier} from "@dynamic_odoo/studio/center/modifier";
import {DashboardWidgets} from "@dynamic_odoo/base/views/dashboard/components/components";


const PROPS = {
    date_stop: {
        optional: true, type: String, modifierProps: {
            widget: "datetime",
        }
    }
}

class ExtendNodeModifier extends NodeModifier {
}

ExtendNodeModifier.nodeProps = {
    ...NodeModifier.nodeProps, ...PROPS
}

ExtendNodeModifier.nodeViewStore = [
    ...NodeModifier.nodeViewStore,
    ["[countdown]", ["date_stop"]]
]

export class CountdownModifier extends ComponentModifier {
}

CountdownModifier.useStructure = true;
// TitleModifier.showNodeRoot = false;
CountdownModifier.NodeModifier = ExtendNodeModifier;
CountdownModifier.ArchTemplate = "dynamic_odoo.Countdown.Layout_1";
CountdownModifier.components = {
    ...ComponentModifier.components,
    ViewComponent: DashboardWidgets.countdown.component,
};
