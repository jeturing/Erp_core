/** @odoo-module **/

import {LoginDesigner} from "../viewer/login_viewer";
import {ComponentModifierTemplate, NodeModifierTemplate} from "@dynamic_odoo/studio/center/template/template_modifier";
import {ListString} from "../widgets/list_string/list_string";

class LoginNodeModifier extends NodeModifierTemplate {
}

const PROPS = {
    placeholder: {type: String, optional: true, modifierProps: {}},
    't-att-href': {type: String, optional: true},
    't-attf-href': {type: String, optional: true},
    class: {type: String, optional: true},
    string: {
        type: String, optional: true, modifierProps: {
            component: ListString,
            onChange: (node, prop, value) => {
                node.children.splice(value[0], 1, value[1]);
            }, widgetProps: (self, node) => {
                const value = [];
                (node.children || []).map((child, index) => {
                    if (typeof child == "string" && child.trim()) {
                        value.push([index, child]);
                    }
                });
                if (!value.length) {
                    value.push([0, ""]);
                }
                return {value: value};
            }
        }
    },
}

LoginNodeModifier.nodeProps = {
    ...NodeModifierTemplate.nodeProps, ...PROPS
}

LoginNodeModifier.nodeViewStore = [
    ...NodeModifierTemplate.nodeViewStore,
    ["[main], [footer], [header], [body], [section], [form], [nav], [img]", ["class", "more", "css"]],
    ["[input]", ["placeholder", "class", "more", "css"]],
    ["[button], [li], [small], [label]", ["string", "class",  "more", "css"]],
    ["[a]", (node) => {
        const view = ["string", "class", "more", "css"];
        if (node.attrs["t-attf-href"]) {
            view.splice(1, 0, "t-attf-href");
        } else if (node.attrs["t-att-href"]) {
            view.splice(1, 0, "t-att-href");
        } else {
            view.splice(1, 0, "href");
        }
        return view;
    }],
    ["[login]", []],
]

export class LoginModifier extends ComponentModifierTemplate {
}

LoginModifier.NodeModifier = LoginNodeModifier;
LoginModifier.ViewComponent = LoginDesigner;


