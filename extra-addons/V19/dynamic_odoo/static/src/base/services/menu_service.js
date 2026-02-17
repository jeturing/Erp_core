/** @odoo-module **/

import { menuService } from "@web/webclient/menus/menu_service";
const _superStart = menuService.start;


menuService.start = async (env) => {
    const menus = await _superStart(env);
    const superSelectM = menus.selectMenu.bind(menus);
    menus['selectMenu'] = async (menu) => {
        await superSelectM(menu);
        if (odoo.studio) {
            const action = env.services.action.currentController.action;
            const state = {
                model: action.res_model,
                menu_id: menu.id,
                view_type: action.views && action.views[0][1],
                action: action.id
            }
            odoo.studio.state = state;
            env.bus.trigger("STUDIO:MENUS-CHANGED");
        }
    }
    return menus;
};
