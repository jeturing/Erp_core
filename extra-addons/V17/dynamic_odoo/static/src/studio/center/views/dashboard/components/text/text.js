/** @odoo-module **/

import {NodeModifier, ComponentModifier} from "@dynamic_odoo/studio/center/modifier";
import {DashboardWidgets} from "@dynamic_odoo/base/views/dashboard/components/components";
import {YoutubeModifier} from "../youtube/youtube";


const PROPS = {
    text: {
        type: String, optional: true, noLabel: true, modifierProps: {
            widget: "html",
        }
    }
}

class ExtendNodeModifier extends NodeModifier {
}

ExtendNodeModifier.nodeProps = {
    ...NodeModifier.nodeProps, ...PROPS
}

ExtendNodeModifier.nodeViewStore = [...NodeModifier.nodeViewStore, ["[rich_text]", ["text"]]]

export class TextModifier extends ComponentModifier {
}

TextModifier.useStructure = true;
TextModifier.showNodeRoot = true;
TextModifier.NodeModifier = ExtendNodeModifier;
TextModifier.ArchTemplate = "dynamic_odoo.RichText.Layout_1";
TextModifier.components = {
    ...ComponentModifier.components, ViewComponent: DashboardWidgets.rich_text.component,
};
