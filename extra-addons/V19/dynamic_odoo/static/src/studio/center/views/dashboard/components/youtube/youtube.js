/** @odoo-module **/

import {NodeModifier, ComponentModifier, ComponentTabsModifier} from "@dynamic_odoo/studio/center/modifier";
import {DashboardWidgets} from "@dynamic_odoo/base/views/dashboard/components/components";

import {xmlToJson, getTemplate} from "@dynamic_odoo/core/utils/view";
import {
    OhTitle, OhGrid, OhData, OhIcon, OhImage,
} from "@dynamic_odoo/core/widgets/drag_component/drag_component";
import {ROOT_MODEL} from "../component_utils";


const PROPS = {
    link: {
        type: String, optional: true, modifierProps: {
            onChange(node, prop, value) {
                node.attrs.link = value ? value.replace("watch?v=", "embed/") : value;
            }
        }
    }
}

class ExtendNodeModifier extends NodeModifier {
}

ExtendNodeModifier.nodeProps = {
    ...NodeModifier.nodeProps, ...PROPS
}

ExtendNodeModifier.nodeViewStore = [...NodeModifier.nodeViewStore, ["[youtube]", ["link"]]]

export class YoutubeModifier extends ComponentModifier {
}

// YoutubeModifier.useStructure = true;
YoutubeModifier.showNodeRoot = true;
YoutubeModifier.NodeModifier = ExtendNodeModifier;
YoutubeModifier.ArchTemplate = "dynamic_odoo.Youtube.Layout_1";
YoutubeModifier.components = {
    ...ComponentModifier.components, ViewComponent: DashboardWidgets.youtube.component,
};
