/** @odoo-module **/

import {KanbanCompiler} from "@web/views/kanban/kanban_compiler";
import {patch} from "@web/core/utils/patch";

patch(KanbanCompiler.prototype, {
    compileButton(el, params) {
        const compiled = super.compileButton(el, params);
        const style = el.getAttribute("style");
        if (style) {
            compiled.setAttribute("style", `'${style}'`);
        }
        return compiled;
    }
});

