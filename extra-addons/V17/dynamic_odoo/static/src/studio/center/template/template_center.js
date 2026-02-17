/** @odoo-module **/

import {xmlToJson} from "@dynamic_odoo/core/utils/view";
import {useModel} from "@web/model/model";
import {TemplateModel} from "./template_model";
import {ComponentModifierTemplate} from "./template_modifier";

const {Component, onMounted, onWillUnmount, xml, onWillStart} = owl;

export class TemplateCenter extends Component {
    setup() {
        this.model = useModel(TemplateModel);
        onWillStart(async () => {
            await this.loadData();
        });
        const onReset = this.onReset.bind(this);
        onMounted(() => {
            this.env.bus.addEventListener("MORE_CENTER:RESET", onReset);
        });
        onWillUnmount(() => {
            this.env.bus.removeEventListener("MORE_CENTER:RESET", onReset);
        });
    }

    get key() {
        return Math.random();
    }

    async loadData() {
        this.canUndoRedo = await this.model.canUndoRedo(this.key);
        this.templateHtml = await this.env.services.orm.call("ir.ui.view", "render_weblogin", []);
    }

    async loadTemplateHtml() {
        return await this.env.services.orm.call("ir.ui.view", "render_weblogin", []);
    }

    get viewInfo() {
        const parser = new DOMParser();
        const xml = parser.parseFromString(this.templateHtml, "text/html");
        const viewInfo = {
            archJson: xmlToJson(xml),
            model: false,
            params: {},
            key: this.key
        }
        return viewInfo;
    }

    async reload() {
        await this.loadData();
        this.render(true);
    }

    async onReset() {
        await this.model.resetTemplate(this.key);
        await this.loadData();
        this.render(true);
    }

    async onUndoRedo(type) {
        if (this.canUndoRedo[`can_${type}`]) {
            await this.model.undoRedoTemplate(this.key, type);
            await this.reload();
            this.env.bus.trigger("TEMPLATE:UNDO-REDO");
        }
    }
}

TemplateCenter.template = "dynamic_odoo.TemplateCenter";
TemplateCenter.components = {Modifier: ComponentModifierTemplate};
