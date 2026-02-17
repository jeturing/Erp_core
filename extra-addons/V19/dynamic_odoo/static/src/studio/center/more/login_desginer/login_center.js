/** @odoo-module **/

import {LoginModifier} from "./modifier/login_modifier";
import {TemplateCenter} from "@dynamic_odoo/studio/center/template/template_center";

export class LoginCenter extends TemplateCenter {

    async loadTemplateHtml() {
        return await this.env.services.orm.call("ir.ui.view", "render_weblogin", []);
    }

    get key() {
        return "web.login";
    }
}

LoginCenter.classes = "login_center";
LoginCenter.components = {Modifier: LoginModifier};
