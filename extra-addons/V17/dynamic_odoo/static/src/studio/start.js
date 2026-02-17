/** @odoo-module **/

import {loadBundle} from "@web/core/assets";
import StudioCenter from "@dynamic_odoo/studio/center/studio_center"

const {Component, onWillDestroy, onWillStart, xml} = owl;

export default class Start extends Component {
    setup() {
        super.setup();
        onWillStart(async () => {
            await this.loadResource();
        });
        const loadModels = this.loadModels.bind(this);
        this.env.bus.addEventListener("START:RELOAD_MODELS", loadModels);
        onWillDestroy(() => {
            this.env.bus.removeEventListener("START:RELOAD_MODELS", loadModels);
        });
    }

    async loadModels() {
        odoo.studio.models = await this.env.services.orm.searchRead("ir.model", [], ["id", "name", "model"]);
    }

    async loadResource() {
        await loadBundle("web_editor.assets_wysiwyg");
        odoo.studio = {
            env: this.env,
            state: false,
            getState: () => odoo.studio.state || this.env.services.router.current.hash
        };
        if (!("models" in odoo.studio)) {
            await this.loadModels();
        }
    }
}

Start.template = xml`<Center />`;
Start.components = {Center: StudioCenter}
