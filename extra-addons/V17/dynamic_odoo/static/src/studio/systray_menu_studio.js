/** @odoo-module **/

import {session} from "@web/session";
import {templates} from "@web/core/assets";
import {registry} from '@web/core/registry';
import Start from '@dynamic_odoo/studio/start';

const {mount, xml, Component} = owl;

const systrayRegistry = registry.category('systray');


export class StudioIcon extends Component {
    get webClient() {
        return document.getElementsByClassName("o_web_client")[0];
    }

    setup() {
        this.env.bus.addEventListener("STUDIO:CLOSE", () => {
            this.onDestroy();
        });
    }

    onDestroy() {
        this.webClient.classList.remove("odoo_studio_mode");
        this.start.__owl__.destroy();
    }

    async onShowCenter() {
        this.start = await
            mount(Start, document.getElementsByClassName("o_action_manager")[0], {
                env: this.env,
                templates: templates,
                position: "first-child"
            });
        this.webClient.classList.add("odoo_studio_mode")
        this.start.render();
    }
}

StudioIcon.prototype.sequence = 1;
StudioIcon.template = xml`
<div class="o-dropdown dropdown o-mail-DiscussSystray-class o-dropdown--no-caret">
    <button class="dropdown-toggle" t-on-click="onShowCenter">
        <img width="12px" height="12px" src="/dynamic_odoo/static/img/studio_icon_mode.png" alt="Odoo Studio Icon" title="Toggle Studio" aria-label="Toggle Studio" />
    </button>
</div>`;
if (session['showStudio']) {
    systrayRegistry.add("dynamic_odoo.StudioMobileIcon", {Component: StudioIcon});
}
