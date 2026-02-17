/** @odoo-module **/
import {Navbar} from "@web/webclient/navbar/navbar";
import {patch} from "@web/core/utils/patch";


// patch(Navbar.prototype, {
//     onNavBarDropdownItemSelection(menu) {
//         super.onNavBarDropdownItemSelection(menu);
//         if (menu) {
//             this.env.bus.trigger("STUDIO:MENUS-CHANGED", {menu: menu});
//         }
//     }
// });
